# SCRIPT --------------------------------------------------------------------------------------------------------------
# Geometry class, mainly based on ESRIs arcpy.Geometry():
# - https://pro.arcgis.com/en/pro-app/latest/arcpy/classes/geometry.htm
# ---------------------------------------------------------------------------------------------------------------------


# LICENSE -------------------------------------------------------------------------------------------------------------
# Copyright 2021 by Markus Schön
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ---------------------------------------------------------------------------------------------------------------------


# CREDITS -------------------------------------------------------------------------------------------------------------
# Thanks to all developers who created the used modules.
# Thanks to FelixIP and BERA from gis.stackexchange.com for the inspiration:
# - https://gis.stackexchange.com/questions/286439/need-tool-for-arcmap-to-draw-circle-touching-three-points
# Thanks to Curtis Price for the rotation inspiration:
# - https://github.com/usgs/arcgis-sample/blob/master/scripts/RotateFeatureClass.py
# ---------------------------------------------------------------------------------------------------------------------


# MODULES -------------------------------------------------------------------------------------------------------------
import json
import math

import arcpy
import numpy as np

# ---------------------------------------------------------------------------------------------------------------------


# GENERAL INFORMATION -------------------------------------------------------------------------------------------------
__author__ = 'Markus Schön'
__copyright__ = 'Copyright 2021 by Markus Schön'
__license__ = 'Apache License, Version 2.0'

__all__ = ['Geometry', 'GeometryError']
# ---------------------------------------------------------------------------------------------------------------------


# EXCEPTIONS ----------------------------------------------------------------------------------------------------------
class GeometryError(Exception):
    """
    Raised when a Geometry method is called with input it cannot process.

    The message is also forwarded to arcpy.AddError(), so it shows up in the ArcGIS Pro message pane when the class is
    used from a script tool.
    """
# ---------------------------------------------------------------------------------------------------------------------


# CLASSES -------------------------------------------------------------------------------------------------------------
class Geometry:
    #: Sort options for numerate(): sort_by -> [xy index, reverse primary axis, reverse secondary axis]
    SORT_OPTIONS = {
        'top_left': [1, True, False],       # [y -> index 1, top 2 bottom -> reverse, left 2 right -> no reverse]
        'top_right': [1, True, True],       # [y -> index 1, top 2 bottom -> reverse, right 2 left -> reverse]
        'bottom_left': [1, False, False],   # [y -> index 1, bottom 2 top -> no reverse, left 2 right -> no reverse]
        'bottom_right': [1, False, True],   # [y -> index 1, bottom 2 top -> no reverse, right 2 left -> reverse]
        'right_top': [0, True, True],       # [x -> index 0, right 2 left -> reverse, top 2 bottom -> reverse]
        'right_bottom': [0, True, False],   # [x -> index 0, right 2 left -> reverse, bottom 2 top -> no reverse]
        'left_top': [0, False, True],       # [x -> index 0, left 2 right -> no reverse, top 2 bottom -> reverse]
        'left_bottom': [0, False, False],   # [x -> index 0, left 2 right -> no reverse, bottom 2 top -> no reverse]
    }

    #: Accepted values for rotate_fc(rotation_value=...)
    ROTATION_VALUES = ('xy', 'in_feature_centroid', 'in_feature_true_centroid')

    def __init__(self, feature):
        """
        This is a collection of geometry functions for ArcGIS Pro.

        Notes:
        - This class is mainly based on ESRIs arcpy.Geometry() class:
          https://pro.arcgis.com/en/pro-app/latest/arcpy/classes/geometry.htm
        - You can use the with-statement.
        - You can use selected features.

        :param str feature: Feature layer or class.
        :rtype: object
        :return: Geometry object
        """

        self.feature = feature
        self.__shape = None
        self.__feature_number = None
        self.__desc = arcpy.Describe(self.feature)

    def __enter__(self):
        """
        Enter the 'with' statement.

        This method is called when the 'with' statement is entered. It creates a geometry instance.

        :rtype: object
        :return: Geometry instance.
        """

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the 'with' statement.

        This method is called when the 'with' statement is exited. It releases the cached geometry objects, freeing up
        the memory they were using. The instance itself stays usable.

        :param exc_type: Exception type.
        :param exc_val: Exception value.
        :param exc_tb: Exception traceback.

        :return: None
        """

        self.__shape = None
        self.__feature_number = None

    @staticmethod
    def _fail(*messages):
        """
        Report an error to ArcGIS Pro and abort the current method.

        :param str messages: One or more error messages.
        :raise GeometryError: Always.
        """

        for message in messages:
            arcpy.AddError(message)

        raise GeometryError(' '.join(messages))

    # Properties
    @property
    def feature_number(self):
        """
        Get number of features (Read Only).
        :rtype: int
        :return: Number of features.
        """

        if self.__feature_number is None:
            self.__feature_number = int(arcpy.GetCount_management(self.feature).getOutput(0))

        return self.__feature_number

    @property
    def shape(self):
        """
        Create a list of geometry objects (Read Only).
        :rtype: list.
        :return: List of geometry objects.
        """

        if self.__shape is None:
            self.__shape = arcpy.CopyFeatures_management(self.feature, arcpy.Geometry())
        return self.__shape

    @property
    def shape_type(self):
        """
        The geometry type: polygon, polyline, point, multipoint, multipatch, dimension, or annotation (Read Only).
        https://pro.arcgis.com/en/pro-app/latest/arcpy/classes/geometry.htm --> Properties --> type

        Hint: The type is read from the feature description. That way it stays available for empty feature classes and
        does not require loading every single geometry.

        :rtype: str
        :return: geometry type.
        """

        return self.__desc.shapeType.lower()

    @property
    def spatial_reference(self):
        """
        The geometry spatial reference (Read Only).
        :rtype: arcpy.SpatialReference
        :return: Geometry spatial reference.
        """

        return self.__desc.spatialReference

    @property
    def has_spatial_reference(self):
        """
        Whether a coordinate system is defined for the feature (Read Only).

        Hint: arcpy returns a spatial reference named 'Unknown' instead of None for undefined coordinate systems, so a
        plain truth test is not enough.

        :rtype: bool
        :return: True if a coordinate system is defined.
        """

        spatial_reference = self.spatial_reference

        return spatial_reference is not None and spatial_reference.name not in ('', 'Unknown')

    @staticmethod
    def _copy_missing_fields(in_feature, out_feature):
        """
        Copy all missing fields from an input feature to another feature class.

        Hint: This is useful when copying geometry to a feature class. In this case we are missing all fields and
        attributes.

        :param str in_feature: Input feature layer/class. The fields will be copied from this feature layer/class
        :param str out_feature: Output feature layer/class. The fields will be added to this feature class.
        """

        # Get accepted field names (from the input feature)
        fields_ignore_names = [x.name for x in arcpy.ListFields(out_feature)] + ['GlobalID']
        fields_accept = [x for x in arcpy.ListFields(in_feature) if x.name not in fields_ignore_names]
        fields_accept_names = [x.name for x in fields_accept]

        if not fields_accept:
            return

        # Add fields_accept to the output feature
        for x in fields_accept:
            arcpy.AddField_management(
                in_table=out_feature,
                field_name=x.name,
                field_type=x.type,
                field_precision=x.precision,
                field_scale=x.scale,
                field_length=x.length,
                field_alias=x.aliasName,
                field_is_nullable=x.isNullable,
                field_is_required=x.required,
                field_domain=x.domain
            )

        # Collect attributes (the row order matches the geometry order the output was created from)
        content = list(arcpy.da.SearchCursor(in_feature, fields_accept_names))

        # Add attributes to fields_accept
        with arcpy.da.UpdateCursor(out_feature, fields_accept_names) as cur:
            for row_counter, row in enumerate(cur):
                row[:] = content[row_counter]
                cur.updateRow(row)

    def boundary(self, out_fc):
        """
        Create a boundary feature class.
        :param str out_fc: Path for the boundary feature class.
        :rtype: str
        :return: Boundary feature class path
        """

        # Create boundary feature class
        boundaries = [x.boundary() for x in self.shape]
        arcpy.CopyFeatures_management(boundaries, out_fc)

        # Copy missing fields and attributes
        self._copy_missing_fields(self.feature, out_fc)

        return out_fc

    def extent(self, out_fc):
        """
        Create an extent feature class.
        :param str out_fc: Path for the extent feature class.
        :rtype: str
        :return: Extent feature class path
        """

        # Create extent feature class
        extents = [x.extent.polygon for x in self.shape]
        arcpy.CopyFeatures_management(extents, out_fc)

        # Copy missing fields and attributes
        self._copy_missing_fields(self.feature, out_fc)

        return out_fc

    def circle_from_three_points(self, out_circle_feature_class, out_circle_centroid_feature_class=None):
        """
        For a given point feature layer, every three point features will be taken to create a circle:
        - https://gis.stackexchange.com/questions/286439/need-tool-for-arcmap-to-draw-circle-touching-three-points
          (--> Thanks to FelixIP and BERA from gis.stackexchange.com for the inspiration).

        Conditions
        - The Geometry class needs to be initialized with a point feature layer/class.
        - The number of the features needs to be a multiple of three --> Every three features will be taken to create a
          circle.

        :param str out_circle_feature_class: Output feature class path for the created circles.
        :param str out_circle_centroid_feature_class: Output feature class path for the created circle centroids.
        :rtype: str
        :return: Output feature class path for the created circles.
        :raise GeometryError: For non-point input, multipart input or a point count that is no multiple of three.
        """

        if self.shape_type != 'point':
            self._fail(
                'The method only works for point feature classes!',
                f"The feature '{self.feature}' has shape type {self.shape_type}!"
            )

        if any(x.isMultipart for x in self.shape):
            self._fail(
                'The method only works for single part feature classes!',
                f"The feature '{self.feature}' has multipart features!"
            )

        if len(self.shape) % 3 != 0:
            self._fail(
                'The method only works for groups of three points!',
                f"The feature '{self.feature}' has {len(self.shape)} points!"
            )

        circle_points = []
        circle_radius = []

        # Group points
        first_points = [p.firstPoint for p in self.shape]
        points_zip = zip(first_points[0::3], first_points[1::3], first_points[2::3])

        for group_index, points in enumerate(points_zip):
            # Calculate centroid coordinates
            matrix = [[p.X, p.Y, 1] for p in points]
            det_a = np.linalg.det(matrix)

            if det_a == 0:
                # There is no solution for the LGS. No point exists with the same distance to all three points.
                arcpy.AddError("There is no solution for the method 'circle_from_three_points'!")
                arcpy.AddError('It does not exist a point with the same distance to all three points!')
                continue

            # An unique solution exists
            matrix = [[(p.X ** 2 + p.Y ** 2) / 2, p.Y, 1] for p in points]
            x = np.linalg.det(matrix) / det_a

            matrix = [[p.X, (p.X ** 2 + p.Y ** 2) / 2, 1] for p in points]
            y = np.linalg.det(matrix) / det_a

            # Create point geometry
            point_geometry = arcpy.PointGeometry(arcpy.Point(x, y), self.spatial_reference)
            circle_points.append(point_geometry)

            # Calculate radius - the first point of the current group lies on the circle
            circle_radius.append(self.shape[group_index * 3].distanceTo(point_geometry))

        if not circle_points:
            return out_circle_feature_class

        # Create feature classes
        if out_circle_centroid_feature_class is None:
            out_circle_centroid_feature_class = r'memory\circle_centroid_fc'

        # Create circle centroids fc
        arcpy.CopyFeatures_management(circle_points, out_circle_centroid_feature_class)

        # - Add radius to the circle centroids fc
        arcpy.AddField_management(out_circle_centroid_feature_class, 'distance', 'Double')
        with arcpy.da.UpdateCursor(out_circle_centroid_feature_class, ['distance']) as cursor:
            for index_counter, row in enumerate(cursor):
                row[0] = circle_radius[index_counter]
                cursor.updateRow(row)

        # Create circle fc
        arcpy.Buffer_analysis(out_circle_centroid_feature_class, out_circle_feature_class, 'distance')

        return out_circle_feature_class

    def convex_hull(self, out_fc):
        """
        Create a convex hull feature class.
        :param str out_fc: Path for the convex hull feature class.
        :rtype: str
        :return: Convex hull feature class path
        """

        # Create convex hull feature class
        convex_hulls = [x.convexHull() for x in self.shape]
        arcpy.CopyFeatures_management(convex_hulls, out_fc)

        # Copy missing fields and attributes
        self._copy_missing_fields(self.feature, out_fc)

        return out_fc

    def hull_rectangle(self, out_fc):
        """
        Create a hull rectangle feature class.
        :param str out_fc: Path for the hull rectangle feature class.
        :rtype: str
        :return: Hull rectangle feature class path
        """

        polygons = []

        # Hint: hullRectangle returns a space delimited string of eight coordinates. Its decimal separator follows the
        # ArcGIS Pro locale, so a comma is replaced by a dot before parsing.
        for coordinate_list in [list(map(float, x.hullRectangle.replace(',', '.').split())) for x in self.shape]:
            array = arcpy.Array()

            for i in range(4):  # Every rectangle has four coordinate pairs
                x = coordinate_list[i * 2]
                y = coordinate_list[i * 2 + 1]
                array.add(arcpy.Point(x, y))

            polygons.append(arcpy.Polygon(array, self.spatial_reference))

        arcpy.CopyFeatures_management(polygons, out_fc)

        # Copy missing fields and attributes
        self._copy_missing_fields(self.feature, out_fc)

        return out_fc

    def cut(self, cut_polyline, out_fc):
        """
        Cut a polyline/polygon by a polyline.
        :param str cut_polyline: The initialized polyline/polygon will be cut by the cut_polyline.
        :param str out_fc: Path for the cut feature class.
        :rtype: str
        :return: Cut feature class path.
        :raise GeometryError: If the cutting feature is no polyline or the initialized feature is a point feature.
        """

        cut_polyline_geom = Geometry(cut_polyline)

        if cut_polyline_geom.shape_type != 'polyline':
            self._fail(f'The cutting polyline has shape type {cut_polyline_geom.shape_type}!')

        if self.shape_type == 'point':
            self._fail('The main feature has shape type "point" and cannot be cut!')

        cut = list(self.shape)
        for cut_pol in cut_polyline_geom.shape:
            cut_add = []  # collect all cut features
            cut_rem = []  # collect all features that will be replaced by cut features

            for x in cut:
                if x.disjoint(cut_pol) is False:
                    cut_add.extend(x.cut(cut_pol))
                    cut_rem.append(x)

            cut = [x for x in cut + cut_add if x not in cut_rem]  # Cut features are replaced by cut for next round

        memory_fc = r'memory\cut_fc'
        try:
            arcpy.CopyFeatures_management(cut, memory_fc)
            arcpy.MultipartToSinglepart_management(memory_fc, out_fc)
        finally:
            arcpy.Delete_management(memory_fc)

        return out_fc

    @staticmethod
    def rank_by_length(combination_lengths, combination_oids, oid_position):
        """
        Rank distance line combinations by their length.

        This is the pure ranking logic behind distance_lines(). It is kept free of arcpy calls so it can be unit tested
        without an ArcGIS Pro license.

        :param dict combination_lengths: Maps a combination key to the length of its distance line.
        :param dict combination_oids: Maps a combination key to the (oid1, oid2) tuple it was built from. The insertion
        order decides how combinations of an equal length are ranked.
        :param int oid_position: 0 to group by the first object id, 1 to group by the second one.

        :rtype: dict
        :return: Maps the string representation of an object id to its combination keys, shortest distance line first.
        """

        ranking = {}

        for combination, oids in combination_oids.items():
            ranking.setdefault(str(oids[oid_position]), []).append(combination)

        for combinations in ranking.values():
            # list.sort() is stable, so combinations of an equal length keep their insertion order
            combinations.sort(key=lambda combination: combination_lengths[combination])

        return ranking

    def distance_lines(self, other_fc, out_fc, overwrite_out_fc=True):
        """
        Create distance lines between the initialized feature layer and the other feature layer 'other_fc'.

        Every distance line carries the object ids of both input features, their coordinates and two length based
        rankings: the position of the line within all lines that start at the same feature of the first/second feature
        class.

        :param str other_fc: 2nd feature class to calculate the distance lines.
        :param str out_fc: Calculated distance lines.
        :param bool overwrite_out_fc: Overwrite the output feature class in case of True. By setting this value to
        False, it is possible to run the script again without creating new distance lines. This could be helpful in case
        of setting new definition queries with the toolbox tool because the script runs faster.
        :rtype: str
        :return: Distance line feature class between all features of the geometry feature class and the other feature
        class.
        :raise GeometryError: For unsupported shape types, multipart input or mismatching coordinate systems.
        """

        # Preparation
        # - In fc - object id columns
        first_fc_id = 'OBJECTID'
        second_fc_id = 'OBJECTID'

        # - Out fc - column names for the ids from the input feature classes
        out_fc_col_oid1 = 'OID1'            # Column name for the ids from the first fc
        out_fc_col_oid2 = 'OID2'            # Column name for the ids from the second fc
        out_fc_col_comb_id = 'OID_Comb'     # Column name for the combined first and second ids

        # - Out fc - column names for the index ranking of the shortest distance lines
        out_fc_col_oid1_index = 'OID1_index'  # Index ranking for the shortest distance lines from the first fc
        out_fc_col_oid2_index = 'OID2_index'  # Index ranking for the shortest distance lines from the second fc

        # - Out fc - column names for the coordinates
        out_fc_col_oid1_x = 'OID1_x'
        out_fc_col_oid1_y = 'OID1_y'
        out_fc_col_oid2_x = 'OID2_x'
        out_fc_col_oid2_y = 'OID2_y'

        # Main part
        if arcpy.Exists(out_fc) and overwrite_out_fc is not True:
            return out_fc

        geom_other = Geometry(other_fc)

        # Validation
        if self.shape_type != 'point':
            self._fail(f"Only point features are accepted, not '{self.shape_type}'")

        if geom_other.shape_type in ['multipoint', 'multipatch', 'dimension', 'annotation']:
            self._fail(
                f"The second feature class has geometry type '{geom_other.shape_type}'. "
                f"Please only use 'polygon', 'polyline' oder 'point'!"
            )

        if any(x.isMultipart for x in self.shape):
            self._fail('The first feature class is not allowed to have multipart!')

        if any(x.isMultipart for x in geom_other.shape):
            self._fail('The seconds feature class is not allowed to have multipart!')

        if not self.has_spatial_reference:
            self._fail('The first feature class needs to have defined a coordinate system!')

        if not geom_other.has_spatial_reference:
            self._fail('The second feature class needs to have defined a coordinate system!')

        if self.spatial_reference.factoryCode != geom_other.spatial_reference.factoryCode:
            self._fail('Both feature classes needs to have defined the same coordinate systems!')

        lines = []    # Collect all smallest distance lines between the feature layer and the other feature layer
        xy_list = []  # Collect the distance line start and end points

        # Case: self.shape_type == 'point'
        # --> Collect the distance lines + their start and endpoints
        for geom_fc_part in self.shape:
            for geom_other_part in geom_other.shape:
                if geom_other.shape_type == 'polyline':
                    geom_other_part = geom_other_part.snapToLine(geom_fc_part)

                elif geom_other.shape_type == 'polygon':
                    geom_other_part = geom_other_part.boundary()
                    geom_other_part = geom_other_part.snapToLine(geom_fc_part)

                geom_centroids = [geom_fc_part.centroid, geom_other_part.centroid]

                lines.append(arcpy.Polyline(arcpy.Array(geom_centroids), self.spatial_reference))
                xy_list.append(geom_centroids)

        # Create distance line feature class
        arcpy.CopyFeatures_management(lines, out_fc)

        # Add attributes
        # - Calculate attributes
        fc_ids = [row[0] for row in arcpy.da.SearchCursor(self.feature, [first_fc_id])]
        other_fc_ids = [row[0] for row in arcpy.da.SearchCursor(other_fc, [second_fc_id])]

        check_dict = {}   # Temporarily collect (oid1, oid2) combinations. Main goal is to fill the delete_dict.
        delete_dict = {}  # Collect all (oid1, oid2) combinations that occur several times. If self.feature and
        # other_fc match, the associated polylines will be deleted.

        counter = 0
        combinations = {}
        for fc_id in fc_ids:
            for other_fc_id in other_fc_ids:
                geom_centroids = xy_list[counter]

                comb = f'({fc_id}, {other_fc_id})'
                comb_inv = f'({other_fc_id}, {fc_id})'

                combinations[counter] = {
                    'oid1': fc_id,
                    'oid2': other_fc_id,
                    'comb': comb,
                    'comb_inv': comb_inv,
                    'oid1_x': geom_centroids[0].X,
                    'oid1_y': geom_centroids[0].Y,
                    'oid2_x': geom_centroids[1].X,
                    'oid2_y': geom_centroids[1].Y
                }

                if check_dict.get(comb) is None and comb != comb_inv:
                    check_dict[comb] = True
                    check_dict[comb_inv] = True
                else:
                    delete_dict[comb] = True

                counter += 1

        del check_dict

        # - Add fields
        arcpy.AddField_management(out_fc, out_fc_col_oid1, 'TEXT')
        arcpy.AddField_management(out_fc, out_fc_col_oid2, 'TEXT')
        arcpy.AddField_management(out_fc, out_fc_col_comb_id, 'TEXT')

        arcpy.AddField_management(out_fc, out_fc_col_oid1_x, 'DOUBLE')
        arcpy.AddField_management(out_fc, out_fc_col_oid1_y, 'DOUBLE')
        arcpy.AddField_management(out_fc, out_fc_col_oid2_x, 'DOUBLE')
        arcpy.AddField_management(out_fc, out_fc_col_oid2_y, 'DOUBLE')

        # - Write field attributes
        combination_lengths = {}  # Maps a combination to the length of its distance line
        combination_oids = {}     # Maps a combination to its (oid1, oid2) tuple
        fields = [
            out_fc_col_oid1, out_fc_col_oid2, out_fc_col_comb_id, 'Shape_Length',
            out_fc_col_oid1_x, out_fc_col_oid1_y, out_fc_col_oid2_x, out_fc_col_oid2_y
        ]
        with arcpy.da.UpdateCursor(out_fc, fields) as cursor:
            for counter, row in enumerate(cursor):
                combination = combinations[counter]
                comb = combination['comb']

                row[0] = combination['oid1']
                row[1] = combination['oid2']
                row[2] = comb

                row[4] = combination['oid1_x']
                row[5] = combination['oid1_y']
                row[6] = combination['oid2_x']
                row[7] = combination['oid2_y']

                cursor.updateRow(row)

                combination_lengths[comb] = row[3]
                combination_oids[comb] = (combination['oid1'], combination['oid2'])

        # Create length based rankings
        # - Map every object id to its combinations, shortest distance line first
        fc_out_dict = self.rank_by_length(combination_lengths, combination_oids, 0)
        other_fc_out_dict = self.rank_by_length(combination_lengths, combination_oids, 1)

        # - Add fields
        arcpy.AddField_management(out_fc, out_fc_col_oid1_index, 'SHORT')
        arcpy.AddField_management(out_fc, out_fc_col_oid2_index, 'SHORT')

        # - Write rankings
        # Hint: When both inputs are the same feature class, every pair shows up twice plus once as its own mirror
        # image. Those rows get deleted, and because they are still part of the ranking, the remaining ranks are
        # shifted by one.
        is_self_join = self.feature == other_fc
        rank_offset = 1 if is_self_join else 0

        fields = [
            out_fc_col_comb_id,
            out_fc_col_oid1,
            out_fc_col_oid2,
            out_fc_col_oid1_index,
            out_fc_col_oid2_index
        ]

        with arcpy.da.UpdateCursor(out_fc, fields) as cursor:
            for counter, row in enumerate(cursor):
                if is_self_join and delete_dict.get(combinations[counter]['comb']) is True:
                    cursor.deleteRow()
                    continue

                comb, oid1, oid2 = row[0:3]
                row[3] = fc_out_dict[oid1].index(comb) - rank_offset
                row[4] = other_fc_out_dict[oid2].index(comb) - rank_offset
                cursor.updateRow(row)

        return out_fc

    def inner_circle(self, out_circle, out_point=None, accuracy=0.01):
        """
        Create maximum inner circles and centroids for the initialized polygon feature layer.
        :param str out_circle: Feature class containing the inner circles.
        :param str out_point: Feature class containing the inner circle centroids.
        :param float accuracy: The calculation accuracy. This is needed to stop the approximation in some cases.
        :rtype: str
        :return: Feature class containing the inner circles.
        """

        def converge_to_the_center(polygon, centroids_list, distances_list):
            """
            Calculate the maximum inner circle centroids by convergence.

            :param polygon: Polygon shape object.
            :param list centroids_list: List of inner circle centroid point geometries.
            :param list distances_list: List of inner circle radius for every inner circle centroid.
            """

            dist = 0

            while True:
                try:
                    feature_boundary = polygon.boundary()
                    feature_centroid = polygon.centroid

                    point_geom = arcpy.PointGeometry(feature_centroid, self.spatial_reference)
                    min_dist = feature_boundary.distanceTo(point_geom)

                    dist += min_dist

                    if min_dist <= accuracy or polygon.pointCount == 2:
                        centroids_list.append(point_geom)
                        distances_list.append(dist)
                        break

                    # Shrink the polygon by its own distance to the boundary and approximate again
                    polygon = polygon.buffer(-min_dist)

                except Exception as e:
                    arcpy.AddMessage(e)
                    break

        delete_list = []

        # Calculate inner circle centroids and radius
        shapes = arcpy.MultipartToSinglepart_management(self.feature, arcpy.Geometry())

        centroid_list = []
        distance_list = []

        for shape in shapes:
            converge_to_the_center(shape, centroid_list, distance_list)

        # Create inner circle centroid feature class
        if out_point is None:
            out_point = r'memory\out_point'
            delete_list.append(out_point)

        arcpy.CopyFeatures_management(centroid_list, out_point)

        # - Add Fields with distance information to inner circle centroid feature class
        arcpy.AddField_management(out_point, 'radius', 'Double')
        with arcpy.da.UpdateCursor(out_point, 'radius') as cursor:
            for counter, row in enumerate(cursor):
                row[0] = distance_list[counter]
                cursor.updateRow(row)

        # Create inner circle feature class
        arcpy.Buffer_analysis(out_point, out_circle, 'radius')

        # Clear memory
        for element in delete_list:
            arcpy.Delete_management(element)

        return out_circle

    @classmethod
    def sort_features(cls, x_y_oid_rows, sort_by='top_left'):
        """
        Sort (x, y, object id) rows by one of the numerate() sort options.

        This is the pure sorting logic behind numerate(). It is kept free of arcpy calls so it can be unit tested
        without an ArcGIS Pro license.

        :param list x_y_oid_rows: Rows of (x, y, object id).
        :param str sort_by: One of the keys of Geometry.SORT_OPTIONS.

        :rtype: list
        :return: The rows, sorted.
        :raise GeometryError: For an unknown sort option.
        """

        if sort_by not in cls.SORT_OPTIONS:
            cls._fail(
                f"Unknown sort option '{sort_by}'!",
                f"Please use one of: {', '.join(sorted(cls.SORT_OPTIONS))}."
            )

        xy_index, reverse_primary, reverse_secondary = cls.SORT_OPTIONS[sort_by]
        secondary_index = (xy_index + 1) % 2

        # Sort by the secondary axis first, then sort by the primary axis. sorted() is stable, so the secondary order
        # survives as the tie breaker.
        rows = sorted(x_y_oid_rows, key=lambda row: row[secondary_index], reverse=reverse_secondary)

        return sorted(rows, key=lambda row: row[xy_index], reverse=reverse_primary)

    def numerate(self, sort_by='top_left', field_name='id'):
        """
        Numerate all features by its coordinates.
        To store the results, this method creates a short integer field. The lowest value is 1.

        :param str sort_by: Feature sort options:
        - top_left:     Sort from top to bottom. Elements with same y are sorted from left to right.
        - top_right:    Sort from top to bottom. Elements with same y are sorted from right to left.
        - bottom_left:  Sort from bottom to top. Elements with same y are sorted from left to right.
        - bottom_right: Sort from bottom to top. Elements with same y are sorted from right to left.
        - right_top:    Sort from right to left. Elements with same x are sorted from top to bottom.
        - right_bottom: Sort from right to left. Elements with same x are sorted from bottom to top.
        - left_top:     Sort from left to right. Elements with same x are sorted from top to bottom.
        - left_bottom:  Sort from left to right. Elements with same x are sorted from bottom to top.
        :param str field_name: Name of the added short integer field.
        :rtype: str
        :return: Name of the added short integer field.
        :raise GeometryError: For non-point input or an unknown sort option.
        """

        if self.shape_type != 'point':
            self._fail('This method only works for point feature classes!')

        # Add numeration field
        if field_name not in [x.name for x in arcpy.ListFields(self.feature)]:
            arcpy.AddField_management(self.feature, field_name, 'Short')

        # Get oid to id (=numeration) dictionary
        oid_x_y_list = list(arcpy.da.SearchCursor(self.feature, ['SHAPE@X', 'SHAPE@Y', 'OID@']))
        oid_x_y_list_sorted = self.sort_features(oid_x_y_list, sort_by)
        oid_2_id_dict = {row[2]: index + 1 for index, row in enumerate(oid_x_y_list_sorted)}

        # Update feature class numeration field
        with arcpy.da.UpdateCursor(self.feature, ['OID@', field_name]) as cur:
            for row in cur:
                row[1] = oid_2_id_dict[row[0]]
                cur.updateRow(row)

        return field_name

    def polyline_to_polygon(self, out_polygon):
        """
        Create a polygon feature class from a polyline feature (layer/class).
        We keep the original spatial reference.

        :param str out_polygon: Output polygon feature class path.

        :rtype: str
        :return: Output polygon feature class path. An empty string if the conversion failed.
        """

        # Get feature set dictionary
        # https://developers.arcgis.com/documentation/common-data-types/featureset-object.htm
        feature_set = arcpy.FeatureSet()
        feature_set.load(self.feature)
        json_dict = json.loads(feature_set.JSON)

        # Edit feature set dictionary
        # - Set geometry type
        json_dict['geometryType'] = 'esriGeometryPolygon'

        # - Set array types
        json_str = json.dumps(json_dict)  # Create string from dictionary

        array_types = {'curvePaths': 'curveRings', 'paths': 'rings'}
        for polyline_array_type, polygon_array_type in array_types.items():
            json_str = json_str.replace(polyline_array_type, polygon_array_type)

        # Save edited feature set dictionary to a polygon feature class
        try:
            fs = arcpy.FeatureSet()
            fs.load(json_str)
            arcpy.CopyFeatures_management(fs, out_polygon)
            arcpy.RepairGeometry_management(out_polygon)

        except AttributeError as e:
            arcpy.AddWarning(f'Spatial reference: {json_dict["spatialReference"]}')
            arcpy.AddWarning(f"Attribute Error:\nThe coordinates doesn't match the coordinate system\n\nOriginal:\n{e}")
            out_polygon = ''

        except Exception as e:
            arcpy.AddWarning(e)
            out_polygon = ''

        return out_polygon

    def points_along_feature(self, out_fc, distance=0.5, include_endpoint=False):
        """
        Creates points along a polyline or polygon feature (layer/class) for a selected distance.
        One multipoint is created for each feature.

        Every multipoint starts at the first point of its feature and continues in steps of 'distance'. The end point is
        only part of the result if 'include_endpoint' is set.

        :param str out_fc: Output feature class path for the created multipoints.
        :param float distance: Distance between each following point.
        :param bool include_endpoint: If True, add endpoint.
        :rtype: str
        :return: Output feature class path. An empty string if the input holds no features.
        :raise GeometryError: For a distance of zero or less and for unsupported shape types.
        """

        if distance <= 0:
            self._fail(f'The distance has to be greater than zero, not {distance}!')

        # Get lines
        if self.shape_type == 'polygon':
            shapes = [x.boundary() for x in self.shape]
        elif self.shape_type == 'polyline':
            shapes = self.shape
        else:
            self._fail(f"The method only works for polyline and polygon feature classes, not '{self.shape_type}'!")

        point_list = []

        # Create multipoints (for every shape)
        for shape in shapes:
            array = arcpy.Array(shape.firstPoint)

            # Hint: The position is derived from the step index instead of being accumulated, so rounding errors cannot
            # add up along a line.
            for step in range(1, int(shape.length / distance) + 1):
                position = step * distance

                if position >= shape.length:
                    # positionAlongLine() clamps to the end point, which would duplicate it
                    break

                array.add(shape.positionAlongLine(position).centroid)

            if include_endpoint:
                array.add(shape.lastPoint)

            point_list.append(arcpy.Multipoint(array, self.spatial_reference))

        # Create out_fc (from collected multipoints)
        if not point_list:
            return ''

        arcpy.CopyFeatures_management(point_list, out_fc)

        return out_fc

    @staticmethod
    def rotate_xy(x, y, rotation_angle=0, x_cnt=0, y_cnt=0):
        """
        Rotate x, y values by center point coordinates x_cnt, y_cnt and a rotation angle.

        # Thanks to Curtis Price for the rotation inspiration:
        # - https://github.com/usgs/arcgis-sample/blob/master/scripts/RotateFeatureClass.py

        :param float x: X value to be rotated.
        :param float y: Y value to be rotated.
        :param float rotation_angle: Number of degrees with which to rotate.
        :param float x_cnt: X value around which to rotate. (x_cnt = abbreviation for 'x center').
        :param float y_cnt: Y value around which to rotate. (y_cnt = abbreviation for 'y center').

        :rtype: tuple
        :return: Tuple (x, y) with rotated xy values.
        """

        # Move x, y to the origin (First we want to rotate through the coordinate origin, and then we move back)
        x -= x_cnt
        y -= y_cnt

        # Get angle radian (clockwise rotation)
        rotation_angle = -1 * rotation_angle  # Factor -1 means clockwise rotation
        rotation_angle = math.radians(rotation_angle)

        # Rotate x, y through the coordinate origin (and then move back)
        x_rot = (x * math.cos(rotation_angle)) - (y * math.sin(rotation_angle)) + x_cnt
        y_rot = (x * math.sin(rotation_angle)) + (y * math.cos(rotation_angle)) + y_cnt

        return x_rot, y_rot

    def rotate_fc(self, out_feature, rotation_value='xy', rotation_angle=0, rotation_x=0, rotation_y=0):
        """
        Rotate an input feature class. Curves will be respected.

        :param str out_feature: Output feature class path.
        :param str rotation_value:
            - 'xy':
               Use the values 'rotation_x' and 'rotation_y' for rotation.
            - 'in_feature_centroid':
               For every feature, the features centroid will be used for rotation. The tool acts like handling single
               part features.
            - 'in_feature_true_centroid':
               For every feature, the features true centroid will be used for rotation. The tool acts like handling
               single part features.
        :param float rotation_angle: Input rotation value.
        :param float rotation_x: (Optional) X value around which to rotate. This value will only be used in case of
        rotation_value = 'xy'.
        :param float rotation_y: (Optional) Y value around which to rotate. This value will only be used in case of
        rotation_value = 'xy'.

        :rtype: str
        :return: Output feature class path.
        :raise GeometryError: For an unknown rotation value.
        """

        if rotation_value not in self.ROTATION_VALUES:
            self._fail(
                f"Unknown rotation value '{rotation_value}'!",
                f"Please use one of: {', '.join(self.ROTATION_VALUES)}."
            )

        # Preparation
        # - Output feature
        if out_feature != self.__desc.catalogPath:
            arcpy.CopyFeatures_management(self.feature, out_feature)

        # - Check shape_type
        if self.shape_type in ['point', 'multipoint'] and rotation_value != 'xy':
            # Centroid rotation - Points do not have to be rotated around themselves.
            return out_feature

        # - Ensure, rotation angle < 360°
        rotation_angle = int(rotation_angle) % 360 + (rotation_angle - int(rotation_angle))

        # - Collect the rotation centroids in case of rotation_value != 'xy'
        in_feature_centroid_list = []  # Feature rotation centroids

        if rotation_value != 'xy':
            feature_mem = r'memory\feature_single_parts'
            arcpy.MultipartToSinglepart_management(out_feature, feature_mem)

            with arcpy.da.SearchCursor(feature_mem, 'SHAPE@') as cur:
                for row in cur:
                    if rotation_value == 'in_feature_centroid':
                        in_feature_centroid_list.append(row[0].centroid)
                    else:
                        in_feature_centroid_list.append(row[0].trueCentroid)

            arcpy.Delete_management(feature_mem)

        # Rotation
        with arcpy.da.UpdateCursor(out_feature, 'SHAPE@JSON') as cur:
            cnt_in_feature_centroid = 0

            for row in cur:
                if row[0] is None:
                    # - Can't rotate NoneType values
                    continue

                row_dict = json.loads(row[0])

                # - Points
                if row_dict.get('x'):
                    # - - Hint: type(row_dict['x']) == float
                    row_dict['x'], row_dict['y'] = self.rotate_xy(
                        row_dict['x'], row_dict['y'], rotation_angle, rotation_x, rotation_y
                    )

                # - MultiPoints
                for key in ['points']:
                    if not row_dict.get(key):
                        continue

                    # - - Hint: type(row_dict[key]) == list
                    for value_list in row_dict[key]:
                        # - - Hint: type(value_list) == list
                        value_list[0], value_list[1] = self.rotate_xy(
                            value_list[0], value_list[1], rotation_angle, rotation_x, rotation_y
                        )

                # - Polylines & Polygons
                for key in ['paths', 'rings', 'curveRings', 'curvePaths']:
                    if not row_dict.get(key):
                        continue

                    # - - Hint: type(row_dict[key]) == list
                    for value_list in row_dict[key]:
                        # - - Hint: type(value_list) == list
                        # - - Check rotation_value - edit rotation_x/y in case of a centroid rotation
                        if rotation_value != 'xy':
                            rotation_x = in_feature_centroid_list[cnt_in_feature_centroid].X
                            rotation_y = in_feature_centroid_list[cnt_in_feature_centroid].Y
                            cnt_in_feature_centroid += 1

                        for iterable in value_list:
                            # - - Hint: type(iterable) in [list, dict]

                            if isinstance(iterable, list):
                                # - - key in ['paths', 'rings']
                                iterable[0], iterable[1] = self.rotate_xy(
                                    iterable[0], iterable[1], rotation_angle, rotation_x, rotation_y
                                )

                            elif isinstance(iterable, dict):
                                # - - key in ['curveRings', 'curvePaths']
                                for sub_key in iterable:
                                    for sub_value in iterable[sub_key]:
                                        # - - Hint: type(sub_value) in [list, int, float]

                                        if isinstance(sub_value, list):
                                            sub_value[0], sub_value[1] = self.rotate_xy(
                                                sub_value[0], sub_value[1], rotation_angle, rotation_x, rotation_y
                                            )

                                        elif not isinstance(sub_value, (int, float)):
                                            arcpy.AddWarning(sub_value)

                # - Save edits
                row[0] = json.dumps(row_dict)
                cur.updateRow(row)

        return out_feature
# ---------------------------------------------------------------------------------------------------------------------
