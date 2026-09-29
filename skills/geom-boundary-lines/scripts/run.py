# -*- coding: utf-8 -*-
"""
提取边界线 —— ArcGIS Pro 版

提取要素的外边界线（可区分外环与内环、按分组输出），用于生成地块外框、范围线、镂空边界。

参数顺序（按工具原定义）：
  1. fc（fc）
  2. out_fc_gdb（out_fc_gdb）
  3. out_fc_name（out_fc_name）

用法：
    python run.py <fc> <out_fc_gdb> <out_fc_name>
"""

import os
import sys

import arcpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _argv(i):
    """替代 arcpy.GetParameterAsText(i)：从命令行取第 i 个参数（字符串）。"""
    if len(sys.argv) > i + 1:
        return sys.argv[i + 1]
    return u""


def _gp(i):
    """替代 arcpy.GetParameter(i)：按常见类型还原命令行参数（数值/布尔/字符串）。"""
    if len(sys.argv) <= i + 1:
        return None
    v = sys.argv[i + 1]
    if v == u"":
        return None
    low = v.lower()
    if low == u"true":
        return True
    if low == u"false":
        return False
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


# SCRIPT --------------------------------------------------------------------------------------------------------------
# ArcGIS Pro script tool: Boundary
# Create a boundary feature class for polygon and polyline feature layer/classes.
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
out_fc_gdb = _argv(1)
out_fc_name = _argv(2)
# ---------------------------------------------------------------------------------------------------------------------


# MAIN PROGRAM --------------------------------------------------------------------------------------------------------
out_fc = output_path(out_fc_gdb, out_fc_name)

# Create boundary
with Geometry(fc) as fc_geom:
    fc_geom.boundary(out_fc)

# Add boundary to content
add_to_active_map(out_fc)
# ---------------------------------------------------------------------------------------------------------------------
