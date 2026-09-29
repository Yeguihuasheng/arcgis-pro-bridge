# SCRIPT --------------------------------------------------------------------------------------------------------------
# ArcGIS Pro script tool: Hull Rectangle
# Create the minimal bounding rectangle for any feature layer/class.
#
# Notes:
# - You can use the dissolve option, to create one hull rectangle for all features.
# - You can work with selected feature layers.
#
# Deprecated: ArcGIS Pro 3.x provides a native tool for this functionality. The leading underscore of the file name
# marks the script as deprecated - it is kept because 'Toolbox.tbx' still references it.
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
from arcgis_pro_geometry._toolbox import add_to_active_map, dissolve, output_path

# ---------------------------------------------------------------------------------------------------------------------


# GENERAL INFORMATION -------------------------------------------------------------------------------------------------
__author__ = 'Markus Schön'
__copyright__ = 'Copyright 2021 by Markus Schön'
__license__ = 'Apache License, Version 2.0'
# ---------------------------------------------------------------------------------------------------------------------


# VARIABLES -----------------------------------------------------------------------------------------------------------
fc = arcpy.GetParameterAsText(0)
dissolve_features = arcpy.GetParameter(1)
out_fc_gdb = arcpy.GetParameterAsText(2)
out_fc_name = arcpy.GetParameterAsText(3)
# ---------------------------------------------------------------------------------------------------------------------


# MAIN PROGRAM --------------------------------------------------------------------------------------------------------
out_fc = output_path(out_fc_gdb, out_fc_name)

# Dissolve fc (optional) and create the hull rectangle
fc = dissolve(fc, dissolve_features)

with Geometry(fc) as fc_geom:
    fc_geom.hull_rectangle(out_fc)

# Add hull rectangle to map
add_to_active_map(out_fc)
# ---------------------------------------------------------------------------------------------------------------------
