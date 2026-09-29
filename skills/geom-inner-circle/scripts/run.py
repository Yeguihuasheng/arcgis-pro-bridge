# -*- coding: utf-8 -*-
"""
最大内切圆 —— ArcGIS Pro 版

为面要素求最大内切圆（多边形内能容纳的最大圆），输出圆心点与圆面，常用于选址可参考的最大空地、交叉口半径等测算。

参数顺序（按工具原定义）：
  1. fc（fc）
  2. out_fc_gdb（out_fc_gdb）
  3. out_fc_circle_name（out_fc_circle_name）
  4. out_fc_circle_centroid_name（out_fc_circle_centroid_name）
  5. accuracy（accuracy）

用法：
    python run.py <fc> <out_fc_gdb> <out_fc_circle_name> <out_fc_circle_centroid_name> <accuracy>
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
# ArcGIS Pro script tool: Inner Circle
# Create maximum inner circles and associated centroids for polygons.
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
out_fc_circle_name = _argv(2)
out_fc_circle_centroid_name = _argv(3)
accuracy = _gp(4)
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
