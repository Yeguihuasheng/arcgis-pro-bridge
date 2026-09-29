# SCRIPT --------------------------------------------------------------------------------------------------------------
# ArcGIS Pro script tool: Inner Circle
# Create maximum inner circles and associated centroids for polygons.
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
import sys
from pathlib import Path

import arcpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arcgis_pro_geometry import Geometry
from arcgis_pro_geometry._toolbox import add_to_active_map, output_path

# ---------------------------------------------------------------------------------------------------------------------


# GENERAL INFORMATION -------------------------------------------------------------------------------------------------
__author__ = 'Markus Schön'
__copyright__ = 'Copyright 2021 by Markus Schön'
__license__ = 'Apache License, Version 2.0'
# ---------------------------------------------------------------------------------------------------------------------


# VARIABLES -----------------------------------------------------------------------------------------------------------
fc = arcpy.GetParameterAsText(0)
out_fc_gdb = arcpy.GetParameterAsText(1)
out_fc_circle_name = arcpy.GetParameterAsText(2)
out_fc_circle_centroid_name = arcpy.GetParameterAsText(3)
accuracy = arcpy.GetParameter(4)
# ---------------------------------------------------------------------------------------------------------------------


# MAIN PROGRAM --------------------------------------------------------------------------------------------------------
out_fc_circle = output_path(out_fc_gdb, out_fc_circle_name)
out_fc_circle_centroid = output_path(out_fc_gdb, out_fc_circle_centroid_name) if out_fc_circle_centroid_name else None

# Create the inner circles (and optionally their centroids)
with Geometry(fc) as fc_geom:
    fc_geom.inner_circle(out_fc_circle, out_fc_circle_centroid, accuracy)

# Add inner circles to content
add_to_active_map(out_fc_circle, out_fc_circle_centroid)
# ---------------------------------------------------------------------------------------------------------------------
