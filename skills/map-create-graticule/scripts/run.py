# -*- coding: utf-8 -*-
"""
生成经纬网 —— ArcGIS Pro 版

按度/分/秒设定的间隔（1 秒 ~ 30 度）生成经纬网线要素（格网），用于标准分幅图框、索引图与制图底图。

参数顺序（按工具原定义）：
  1. degrees（degrees）
  2. minutes（minutes）
  3. seconds（seconds）
  4. out_feature_class（out_feature_class）
  5. 参考数据集（可选，用于取范围与坐标系；经桥执行时必填）

用法：
    python run.py <degrees> <minutes> <seconds> <out_feature_class> [参考数据集]
"""

import os
import sys

import arcpy


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


# -----------------------------------------------
# Name: Create Graticule
# Purpose: Creates graticule of desired interval ranging from 1 second to 30 degrees
# ArcGIS Version: 10.3
# Python Version 2.6
# PEP8
# -----------------------------------------------

try:
    import arcpy
    import sys
    import traceback

    def dms_to_dd(deg, mins, secs):
        """Convert degrees, minutes and seconds into decimal degrees

        Keyword arguments:
        deg     -- Degrees
        mins    -- minutes
        secs    -- seconds
        """
        return deg + (mins / 60.0) + (secs / 3600.0)

    # arcpy environment settings
    arcpy.env.workspace = r'in_memory'
    arcpy.env.scratchWorkspace = r'in_memory'
    arcpy.env.overwriteOutput = True

    # ArcGIS tool parameters
    degrees = int(_argv(0))  # degrees
    minutes = int(_argv(1))  # minutes
    seconds = int(_argv(2))  # seconds
    out_feature_class = _argv(3)  # Output feature class

    # 经纬网的范围与坐标系原实现取自「当前地图」（ArcMap 的 arcpy.mapping），
    # 而 arcpy.mapping 在 Pro 里根本不存在、桥（后台线程）也拿不到 CURRENT。
    # 这里改为：优先用第 5 个参数「参考数据集」取范围与坐标系（桥里可用）；
    # 没给参考数据时再退回当前地图（只能在 Pro 的 Python 窗口主线程跑）。
    ref_dataset = _argv(4)
    if ref_dataset and arcpy.Exists(ref_dataset):
        dsc = arcpy.Describe(ref_dataset)
        sr = dsc.spatialReference
        arcpy.env.outputCoordinateSystem = sr
        extent = dsc.extent
        lower_left = extent.lowerLeft
        upper_right = extent.upperRight
    else:
        aprx = (_ for _ in ()).throw(RuntimeError('CURRENT disabled: run in bridge mode'))
        data_frame = aprx.activeMap
        sr = data_frame.spatialReference
        arcpy.env.outputCoordinateSystem = sr
        extent = data_frame.defaultView.camera.getExtent()
        lower_left = extent.lowerLeft
        upper_right = extent.upperRight
    interval_param = dms_to_dd(degrees, minutes, seconds)
    arcpy.AddMessage("Extent calculated.")

    # Construct coordinate variables for Fishnet. Round so that they fall on a line of lat and long.
    origin_coord = str(round(lower_left.X)) + ' ' + str(round(lower_left.Y))
    corner_coord = str(round(upper_right.X)) + ' ' + str(round(upper_right.Y))
    orient_coord = str(round(lower_left.X)) + ' ' + str(round(lower_left.Y + 10))  # Add 10 to Y for orientation
    fishnet = arcpy.CreateFishnet_management("fishnet", origin_coord, orient_coord, interval_param, interval_param,
                                             corner_coord=corner_coord, geometry_type="POLYLINE")
    arcpy.AddMessage("Fishnet created.")

    # Create fields and perform field calculation
    arcpy.AddField_management(fishnet, "LINE", "TEXT", field_length=20)
    arcpy.AddField_management(fishnet, "DMS", "TEXT", field_length=50)

    line_codeblock = """def line_orientation(line):
        firstX = line.firstPoint.X
        firstY = line.firstPoint.Y
        lastX = line.lastPoint.X
        lastY = line.lastPoint.Y
        if abs(firstX - lastX) < abs(firstY - lastY):
            return "Longitude"
        else:
            return "Latitude"
            """

    dms_codeblock = ("""def dd_to_dms (orientation, shape):
        if orientation == "Latitude":
            dd = round(shape.firstPoint.Y, 3)
        elif orientation ==  "Longitude":
            dd = round(shape.firstPoint.X, 3)
        degrees = int(dd)
        minutes = int(60 * (dd - degrees))
        seconds = 60 * (60 * (dd - degrees) - minutes)

        if orientation == "Longitude":
            if degrees < 0:
                direction = "W"
            elif degrees > 0:
                direction = "E"
            else:
                direction = ""
        elif orientation == "Latitude":
            if degrees < 0:
                direction = "S"
            elif degrees > 0:
                direction = "N"
            else:
                direction = ""
        notation = str(abs(degrees)) + ":" + str(abs(minutes))"""
        """+ ":" + str(abs(seconds)) + " " + direction
        return notation
        """)

    arcpy.CalculateField_management(fishnet, "LINE", "line_orientation (!Shape!)",
                                    "PYTHON_9.3", line_codeblock)
    arcpy.CalculateField_management(fishnet, "DMS", "dd_to_dms (!LINE!, !Shape!)",
                                    "PYTHON_9.3", dms_codeblock)
    arcpy.AddMessage("Fields calculated.")

    # Densify so there are enough intermediate vertices so graticule lines 'curve' when projected.
    densify_distance = interval_param/3.00
    arcpy.Densify_edit(fishnet, 'DISTANCE', densify_distance)
    arcpy.AddMessage("Densify complete.")

    # Create output feature class
    arcpy.CopyFeatures_management(fishnet, out_feature_class)

except:
    tb = sys.exc_info()[2]  # Traceback object
    tbinfo = traceback.format_tb(tb)[0]  # Traceback string
    # Concatenate error information and return to GP window
    pymsg = ('PYTHON ERRORS:\nTraceback info:\n' + tbinfo + '\nError Info: \n'
            + str(sys.exc_info()[1]))
    msgs = 'ArcPy ERRORS:\n' + arcpy.GetMessage(2) + '\n'
    arcpy.AddError(msgs)
    print(pymsg)
finally:
    # Delete in_memory
    arcpy.Delete_management('in_memory')

# End of script
