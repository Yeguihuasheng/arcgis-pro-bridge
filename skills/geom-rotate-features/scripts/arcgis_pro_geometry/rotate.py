# SCRIPT --------------------------------------------------------------------------------------------------------------
# ArcGIS Pro script tool: Rotate
# Rotate a feature layer/class by different rotation methods.
#
# Rotation methods:
# - 'coordinates':               Rotate around the tool parameters 'Rotation - x' and 'Rotation - y'.
# - 'extent middle point':       Rotate around the middle point of the extent of the chosen feature layer/class.
# - 'point feature':             Rotate around the first point of the chosen point feature layer/class.
# - 'in_feature_centroid':       Rotate every feature around its own centroid.
# - 'in_feature_true_centroid':  Rotate every feature around its own true centroid.
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
# Thanks to Curtis Price for the rotation inspiration:
# - https://github.com/usgs/arcgis-sample/blob/master/scripts/RotateFeatureClass.py
# ---------------------------------------------------------------------------------------------------------------------


# MODULES -------------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path

import arcpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arcgis_pro_geometry import Geometry
from arcgis_pro_geometry._toolbox import add_to_active_map, output_path, remove_from_active_map

# ---------------------------------------------------------------------------------------------------------------------


# GENERAL INFORMATION -------------------------------------------------------------------------------------------------
__author__ = 'Markus Schön'
__copyright__ = 'Copyright 2021 by Markus Schön'
__license__ = 'Apache License, Version 2.0'
# ---------------------------------------------------------------------------------------------------------------------


# VARIABLES -----------------------------------------------------------------------------------------------------------
fc = arcpy.GetParameterAsText(0)
out_fc_gdb = arcpy.GetParameterAsText(1)
out_fc_name = arcpy.GetParameterAsText(2)
rotation_angle = arcpy.GetParameter(3)
rotation_method = arcpy.GetParameterAsText(4)
# Hint: rotation_method in
# ['coordinates', 'extent middle point', 'point feature', 'in_feature_centroid', 'in_feature_true_centroid']
feature_layer = arcpy.GetParameterAsText(5)
point_feature_layer = arcpy.GetParameterAsText(6)
rotation_x = arcpy.GetParameter(7)
rotation_y = arcpy.GetParameter(8)

#: Rotation methods that rotate every feature around its own centroid
CENTROID_METHODS = ('in_feature_centroid', 'in_feature_true_centroid')
# ---------------------------------------------------------------------------------------------------------------------


# FUNCTIONS -----------------------------------------------------------------------------------------------------------
def fail(message):
    """
    Report an error to ArcGIS Pro and stop the tool.

    :param str message: Error message.
    """

    arcpy.AddError(message)
    sys.exit(1)


def extent_middle_point(feature):
    """
    Get the middle point of the extent of a feature layer/class.

    :param str feature: Feature layer or class.

    :rtype: tuple
    :return: Tuple (x, y) of the extent middle point.
    """

    if not feature:
        fail("The rotation method 'extent middle point' needs the optional parameter '[IN]: Feature (layer/class)'!")

    extent = arcpy.Describe(feature).extent

    return extent.XMin + 0.5 * extent.width, extent.YMin + 0.5 * extent.height


def first_point(feature):
    """
    Get the coordinates of the first point of a point feature layer/class.

    :param str feature: Point feature layer or class.

    :rtype: tuple
    :return: Tuple (x, y) of the first point.
    """

    if not feature:
        fail(
            "The rotation method 'point feature' needs the optional parameter "
            "'[IN]: Point feature (class/layer)'!"
        )

    with arcpy.da.SearchCursor(feature, ['SHAPE@XY']) as cursor:
        for row in cursor:
            return row[0]

    fail(f"The point feature '{feature}' does not hold any feature to rotate around!")

    return None
# ---------------------------------------------------------------------------------------------------------------------


# MAIN PROGRAM --------------------------------------------------------------------------------------------------------
out_fc = output_path(out_fc_gdb, out_fc_name)

# Set rotation type and rotation center
# Hint: The toolbox offers the method names with spaces; underscores are accepted as well.
rotation_method_key = rotation_method.strip().lower().replace(' ', '_')

if rotation_method_key in CENTROID_METHODS:
    # Use the centroid of every single feature for rotation
    rotation_type = rotation_method_key

else:
    # Use selected xy data for rotation
    rotation_type = 'xy'

    if rotation_method_key == 'extent_middle_point':
        rotation_x, rotation_y = extent_middle_point(feature_layer)

    elif rotation_method_key == 'point_feature':
        rotation_x, rotation_y = first_point(point_feature_layer)

    elif rotation_method_key != 'coordinates':
        fail(f"Unknown rotation method '{rotation_method}'!")

    arcpy.AddMessage(f'Rotating around x={rotation_x}, y={rotation_y}')

# Rotate
with Geometry(fc) as fc_geom:
    out_fc = fc_geom.rotate_fc(out_fc, rotation_type, rotation_angle, rotation_x, rotation_y)

# Add out_fc to the current active map
if out_fc:
    # Remove the previous layer first - it would keep a lock on an overwritten feature class
    remove_from_active_map(out_fc_name)
    add_to_active_map(out_fc)
# ---------------------------------------------------------------------------------------------------------------------
