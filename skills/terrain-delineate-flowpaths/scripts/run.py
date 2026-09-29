# -*- coding: utf-8 -*-
"""
汇流路径提取 —— ArcGIS Pro 版

以 DEM 与洼地（汇水点）多边形为输入，追踪并提取汇流路径，输出汇流路径线要素。

参数顺序（按工具原定义）：
  1. DEMRasterPath（DEMRasterPath）
  2. SinkPolyPath（SinkPolyPath）
  3. OutputPath（OutputPath）

用法：
    python run.py <DEMRasterPath> <SinkPolyPath> <OutputPath>
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


__author__ = 'Qiush'
import arcpy
import os

def DelineateCatchment(DEMRasterPath,SinkPolyPath,OutputPath):
    arcpy.CheckOutExtension("Spatial")
    workspace = os.path.split(OutputPath)[0]
    arcpy.env.workspace = workspace
    arcpy.env.overwriteOutput = True

    if arcpy.Exists(DEMRasterPath) == False:
        print("The input raster does not exist")
        quit()

    if (os.path.splitext(OutputPath)[1].lower() == ".shp"):
        FieldOID = "FID"
        FlowDirection = os.path.join(workspace,"FlowDirection.tif")
        SinkRaster = os.path.join(workspace,"SinkRaster.tif")
        Watershed = os.path.join(workspace,"Watershed.tif")
        Catchment = os.path.join(workspace,"Catchment.shp")


    else:
        FieldOID = "OBJECTID"
        FlowDirection = os.path.join(workspace,"FlowDirection")
        SinkRaster = os.path.join(workspace,"SinkRaster")
        Watershed = os.path.join(workspace,"Watershed")
        Catchment = os.path.join(workspace,"Catchment")

    input_dem = arcpy.Raster(DEMRasterPath)
    flow_direction = arcpy.sa.FlowDirection(input_dem)
    flow_direction.save(FlowDirection)

    cell_size = input_dem.meanCellWidth
    arcpy.env.extent = input_dem.extent
    arcpy.PolygonToRaster_conversion(SinkPolyPath,FieldOID,SinkRaster,"CELL_CENTER","NONE",cell_size)

    watershed = arcpy.sa.Watershed(flow_direction,SinkRaster,"Value")
    watershed.save(Watershed)

    arcpy.RasterToPolygon_conversion(watershed,Catchment,"NO_SIMPLIFY","Value")

    return OutputPath

# DEMRasterPath = r"C:\temp\flow\testdata.gdb\dem_final"
# OutputPath = r"C:\temp\flow\testdata.gdb\catchment"
# SinkPolyPath = r"C:\temp\flow\testdata.gdb\sink_poly"

DEMRasterPath = _argv(0)
SinkPolyPath = _argv(1)
OutputPath = _argv(2)

DelineateCatchment(DEMRasterPath,SinkPolyPath,OutputPath)
