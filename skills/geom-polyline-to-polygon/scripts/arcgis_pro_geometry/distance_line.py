# SCRIPT --------------------------------------------------------------------------------------------------------------
# ArcGIS Pro script tool: Distance Line
# Create a feature class with distance lines between two feature classes, for a currently opened ArcGIS Pro project.
# Moreover, the script applies the *.lyrx-file and the definition query.
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
# ---------------------------------------------------------------------------------------------------------------------


# MODULES -------------------------------------------------------------------------------------------------------------
import os
import sys
from pathlib import Path

import arcpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arcgis_pro_geometry import Geometry
from arcgis_pro_geometry._toolbox import PROJECT_ROOT, active_map, output_path

# ---------------------------------------------------------------------------------------------------------------------


# GENERAL INFORMATION -------------------------------------------------------------------------------------------------
__author__ = 'Markus Schön'
__copyright__ = 'Copyright 2021 by Markus Schön'
__license__ = 'Apache License, Version 2.0'
# ---------------------------------------------------------------------------------------------------------------------


# VARIABLES -----------------------------------------------------------------------------------------------------------
point_fc = arcpy.GetParameterAsText(0)
distance_fc = arcpy.GetParameterAsText(1)
out_fc_gdb = arcpy.GetParameterAsText(2)
out_fc_name = arcpy.GetParameterAsText(3)
overwrite = arcpy.GetParameter(4)
content_number_shortest_distance_from_point_fc = arcpy.GetParameter(5)
content_number_longest_distance_from_point_fc = arcpy.GetParameter(6)
content_number_shortest_distance_from_distance_fc = arcpy.GetParameter(7)
content_number_longest_distance_from_distance_fc = arcpy.GetParameter(8)
content_lyr_display_name = arcpy.GetParameterAsText(9)
content_lyr_unit = arcpy.GetParameter(10)

# In fc - object id column
objectid = 'OBJECTID'

# Out fc - column names for the index ranking of the shortest/longest distance lines
out_fc_col_oid1_index = 'OID1_index'  # Index ranking for the shortest distance lines from the first fc
out_fc_col_oid2_index = 'OID2_index'  # Index ranking for the shortest distance lines from the second fc

# Label expressions per length unit
label_expressions = {
    'meters': 'Round([Shape_Length], 2)&"m"',
    'kilometre': 'Round([Shape_Length]/1000, 2)&"km"',
}
# ---------------------------------------------------------------------------------------------------------------------


# PATHS ---------------------------------------------------------------------------------------------------------------
out_fc = output_path(out_fc_gdb, out_fc_name)
lyrx_file = os.path.join(PROJECT_ROOT, 'data', 'layer', 'distance_lines.lyrx')
# ---------------------------------------------------------------------------------------------------------------------


# FUNCTIONS -----------------------------------------------------------------------------------------------------------
def make_int(value):
    """
    Convert a tool parameter to an integer.

    :param value: Tool parameter value.

    :rtype: int or None
    :return: The value as integer, or None for an empty parameter.
    """

    return int(value) if value else None


def feature_count(feature):
    """
    Count the features of a feature layer/class.

    :param str feature: Feature layer or class.

    :rtype: int
    :return: Number of features.
    """

    return int(arcpy.GetCount_management(feature).getOutput(0))


def build_definition_query():
    """
    Build the definition query for the distance line layer.

    The query keeps the n shortest and/or n longest distance lines per feature of both input feature classes. If both
    input feature classes are the same, the rankings of both directions have to be taken into account.

    :rtype: str
    :return: Definition query. An empty string if no filter was requested.
    """

    is_self_join = point_fc == distance_fc
    conditions = []

    # - n shortest distance lines, seen from the point feature class
    number = make_int(content_number_shortest_distance_from_point_fc)
    if number:
        threshold = number - 1

        if is_self_join:
            conditions.append(f'"{out_fc_col_oid1_index}" <= {threshold} OR "{out_fc_col_oid2_index}" <= {threshold}')
        else:
            conditions.append(f'"{out_fc_col_oid1_index}" <= {threshold}')

    # - n shortest distance lines, seen from the distance feature class
    number = make_int(content_number_shortest_distance_from_distance_fc)
    if number:
        threshold = number - 1

        if is_self_join:
            conditions.append(f'"{out_fc_col_oid1_index}" <= {threshold} OR "{out_fc_col_oid2_index}" <= {threshold}')
        else:
            conditions.append(f'"{out_fc_col_oid2_index}" <= {threshold}')

    # - n longest distance lines, seen from the point feature class
    number = make_int(content_number_longest_distance_from_point_fc)
    if number:
        threshold = feature_count(distance_fc) - number

        if is_self_join:
            conditions.append(
                f'"{out_fc_col_oid1_index}" >= {threshold - 1} OR "{out_fc_col_oid2_index}" >= {threshold - 1}'
            )
        else:
            conditions.append(f'"{out_fc_col_oid1_index}" >= {threshold}')

    # - n longest distance lines, seen from the distance feature class
    number = make_int(content_number_longest_distance_from_distance_fc)
    if number:
        threshold = feature_count(point_fc) - number

        if is_self_join:
            conditions.append(
                f'"{out_fc_col_oid1_index}" >= {threshold - 1} OR "{out_fc_col_oid2_index}" >= {threshold - 1}'
            )
        else:
            conditions.append(f'"{out_fc_col_oid2_index}" >= {threshold}')

    return ' OR '.join(conditions)


def apply_labels(layer):
    """
    Switch on the distance labels of a layer and set the label expression for the chosen length unit.

    :param layer: Layer object.
    """

    if not layer.supports('SHOWLABELS'):
        return

    layer.showLabels = True

    expression = label_expressions.get(content_lyr_unit)

    if not expression:
        # Unknown unit - keep the label expression of the *.lyrx-file
        return

    for label_class in layer.listLabelClasses():
        label_class.expression = expression
# ---------------------------------------------------------------------------------------------------------------------


# MAIN PROGRAM --------------------------------------------------------------------------------------------------------
# Create distance lines
with Geometry(point_fc) as geom_fc:
    geom_fc.distance_lines(distance_fc, out_fc, overwrite_out_fc=overwrite)

# Add out_fc to the current active map
current_map = active_map()

if current_map:
    definition_query = build_definition_query()

    if overwrite is False:
        # Reuse the layer that is already part of the map - this is the fast path for changing the definition query
        layers = current_map.listLayers(content_lyr_display_name)

        if layers:
            layers[0].definitionQuery = definition_query
            apply_labels(layers[0])

        else:
            arcpy.AddError(
                "when using the option 'overwrite = False', u have to add the distance lines to the content. "
                'Please use the self defined display name to identify the content layer.'
            )

    else:
        # - Add out_fc and the *.lyrx-file to the content
        in_layer_out_fc = current_map.addDataFromPath(out_fc)
        in_layer_lyr = current_map.addDataFromPath(lyrx_file)

        # - Point the symbolized layer to the new feature class
        in_layer_lyr.updateConnectionProperties(in_layer_lyr.connectionProperties, in_layer_out_fc.connectionProperties)

        # - Remove the unsymbolized out_fc from the current active map
        current_map.removeLayer(in_layer_out_fc)

        # - Set name, definition query and labels
        in_layer_lyr.name = content_lyr_display_name
        in_layer_lyr.definitionQuery = definition_query
        apply_labels(in_layer_lyr)
# ---------------------------------------------------------------------------------------------------------------------
