# -*- coding: utf-8 -*-
"""
要素旋转 —— ArcGIS Pro 版

把要素绕指定中心按角度旋转（支持按字段取值逐要素旋转、绕要素自身中心或质心旋转），用于道路、地块、设备的朝向调整。

参数顺序（按工具原定义）：
  1. fc（fc）
  2. out_fc_gdb（out_fc_gdb）
  3. out_fc_name（out_fc_name）
  4. rotation_angle（rotation_angle）
  5. rotation_method（rotation_method）
  6. feature_layer（feature_layer）
  7. point_feature_layer（point_feature_layer）
  8. rotation_x（rotation_x）
  9. rotation_y（rotation_y）

用法：
    python run.py <fc> <out_fc_gdb> <out_fc_name> <rotation_angle> <rotation_method> <feature_layer> <point_feature_layer> <rotation_x> <rotation_y>
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


#
#
#
#  Unless required by applicable law or agreed to in writing, software
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# ---------------------------------------------------------------------------------------------------------------------


# Thanks to Curtis Price for the rotation inspiration:
# ---------------------------------------------------------------------------------------------------------------------


# MODULES -------------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path

import arcpy

from arcgis_pro_geometry import Geometry
from arcgis_pro_geometry._toolbox import add_to_active_map, output_path, remove_from_active_map

# ---------------------------------------------------------------------------------------------------------------------


# GENERAL INFORMATION -------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------


# VARIABLES -----------------------------------------------------------------------------------------------------------
fc = _argv(0)
out_fc_gdb = _argv(1)
out_fc_name = _argv(2)
rotation_angle = _gp(3)
rotation_method = _argv(4)
# Hint: rotation_method in
# ['coordinates', 'extent middle point', 'point feature', 'in_feature_centroid', 'in_feature_true_centroid']
feature_layer = _argv(5)
point_feature_layer = _argv(6)
rotation_x = _gp(7)
rotation_y = _gp(8)

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
