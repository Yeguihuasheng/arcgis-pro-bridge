# -*- coding: utf-8 -*-
"""
按线切割要素 —— ArcGIS Pro 版

用切割线把面/线要素切成多个要素，输出切割结果，用于按规划界线、道路中心线切分地块。

参数顺序（按工具原定义）：
  1. fc（fc）
  2. cut_polyline（cut_polyline）
  3. out_fc_gdb（out_fc_gdb）
  4. out_fc_name（out_fc_name）

用法：
    python run.py <fc> <cut_polyline> <out_fc_gdb> <out_fc_name>
"""

import os
import sys

import arcpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _argv(i):
    """替代 arcpy.GetParameterAsText(i)：从命令行取第 i 个参数。"""
    if len(sys.argv) > i + 1:
        return sys.argv[i + 1]
    return u""


# SCRIPT --------------------------------------------------------------------------------------------------------------
# ArcGIS Pro script tool: Cut
# Cut a polyline or polygon feature layer/class by a cutting polyline.
# ---------------------------------------------------------------------------------------------------------------------


#
#
#
#  Unless required by applicable law or agreed to in writing, software
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# ---------------------------------------------------------------------------------------------------------------------


# Thanks to all developers who created the used modules.
# ---------------------------------------------------------------------------------------------------------------------


# MODULES -------------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path

import arcpy

from arcgis_pro_geometry import Geometry
from arcgis_pro_geometry._toolbox import add_to_active_map, output_path

# ---------------------------------------------------------------------------------------------------------------------


# GENERAL INFORMATION -------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------


# VARIABLES -----------------------------------------------------------------------------------------------------------
fc = _argv(0)
cut_polyline = _argv(1)
out_fc_gdb = _argv(2)
out_fc_name = _argv(3)
# ---------------------------------------------------------------------------------------------------------------------


# MAIN PROGRAM --------------------------------------------------------------------------------------------------------
out_fc = output_path(out_fc_gdb, out_fc_name)

# Cut the feature
with Geometry(fc) as fc_geom:
    fc_geom.cut(cut_polyline, out_fc)

# Add cut feature class to content
add_to_active_map(out_fc)
# ---------------------------------------------------------------------------------------------------------------------
