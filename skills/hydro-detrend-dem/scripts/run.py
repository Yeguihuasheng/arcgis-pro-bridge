# -*- coding: utf-8 -*-
"""
河道 DEM 去趋势 —— ArcGIS Pro 版

按流线与流线点的高程对 DEM 做去趋势处理，移除河流的纵向坡度，得到「去趋势 DEM」，是提取水面范围与河道坡度的基础。需要 3D 与 Spatial 许可。

参数顺序（按工具原定义）：
  1. feature_dataset（feature_dataset）
  2. flowline（flowline）
  3. flowline_points（flowline_points）
  4. dem（dem）
  5. buffer_distance（buffer_distance）

用法：
    python run.py <feature_dataset> <flowline> <flowline_points> <dem> <buffer_distance>
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


"""____________________________________________________________________________
Script Name:          _07_DetrendDEM.py
Description:          Creates a detrended DEM.
Date:                 01/14/2020

Usage:
This tool is based on the detrending method used in the River Bathymetry
Toolkit (RBT) http://essa.com/tools/river-bathymetry-toolkit-rbt/.

Parameters:
feature_dataset (str) -- Path to the feature dataset.
flowline (str)        -- Path to the flowline feature class.
flowline_points (str) -- Path to the flowline_points feature class.
dem (str)             -- Path to the digital elevation model (DEM).
buffer_distance (int) -- Distance the flowline_points feature class will be
                         buffered to define the extent of the output
                         detrended DEM. Units are defined by the coordinate
                         system of the DEM.

Outputs:
detrend               -- a new detrended DEM
____________________________________________________________________________"""

import os
from datetime import datetime
import arcpy
from arcpy.sa import *

def DetrendDEM(feature_dataset, flowline, flowline_points, dem, buffer_distance):
    arcpy.CheckOutExtension("3D")
    arcpy.CheckOutExtension("Spatial")

    # Determine the resolution of dem (assumes planar coordinate system)
    cellsize = float(arcpy.GetRasterProperties_management(
                                         dem, "CELLSIZEX").getOutput(0))

    # Set environment variables
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = os.path.dirname(feature_dataset)
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem
    arcpy.env.cellSize = cellsize
    arcpy.env.compression = "LZ77"
    arcpy.env.outputCoordinateSystem = dem

    # List parameter values
    arcpy.AddMessage("Workspace: {}".format(arcpy.env.workspace))
    arcpy.AddMessage("Flowline: "
                     "{}".format(arcpy.Describe(flowline).baseName))
    arcpy.AddMessage("Flowline Points: "
                     "{}".format(arcpy.Describe(flowline_points).baseName))
    arcpy.AddMessage("DEM: {}".format(arcpy.Describe(dem).baseName))
    arcpy.AddMessage("Buffer Distance: {}".format(str(buffer_distance)))

    # Buffer the flowline_points
    flowline_buffer = os.path.join(feature_dataset, "flowline_buffer")
    arcpy.Buffer_analysis(in_features = flowline,
                          out_feature_class = flowline_buffer,
                          buffer_distance_or_field = buffer_distance,
                          line_side = "FULL",
                          line_end_type = "ROUND",
                          dissolve_option = "ALL")
    arcpy.AddMessage("Buffering flowline complete.")

    # Set the environment mask to the flowline_buffer to clip all rasters
    arcpy.AddMessage("Setting mask to flowline_buffer...")
    arcpy.env.mask = flowline_buffer
    arcpy.AddMessage("Setting mask to flowline_buffer complete.")

    # Create the trend raster
    arcpy.AddMessage("Creating trend raster...")
    trend = os.path.join(arcpy.env.workspace, "trend")
    arcpy.Idw_3d(in_point_features = flowline_points,
                 z_field = "Z",
                 out_raster = trend,
                 power = 2,
                 search_radius = "VARIABLE")

    arcpy.AddMessage("Created trend raster.")

    # Smooth the trend raster
    trend_smooth = arcpy.sa.FocalStatistics(
                             in_raster = trend,
                             neighborhood = arcpy.sa.NbrCircle(50, "CELL"),
                             statistics_type = "Mean")
    trend_smooth_path = os.path.join(arcpy.env.workspace, "trend_smooth")
    arcpy.CopyRaster_management(in_raster = trend_smooth,
                                out_rasterdataset = trend_smooth_path)
    arcpy.AddMessage("Smoothed trend raster.")

    # Create the detrended raster
    detrend = (Raster(dem) - Raster(trend_smooth_path)) + float(100)
    detrend_path = os.path.join(arcpy.env.workspace, "detrend")
    arcpy.CopyRaster_management(in_raster = detrend,
                                out_rasterdataset = detrend_path)
    arcpy.AddMessage("Created detrended raster.")

    # Calculate raster statistics and build pyramids
    arcpy.CalculateStatistics_management(detrend_path)
    arcpy.BuildPyramids_management(detrend_path)
    arcpy.AddMessage("Calculated raster statistics and pyramids.")

    # Return
    arcpy.SetParameter(5, detrend_path)

    # Cleanup
    arcpy.Delete_management(in_data = flowline_buffer)
    arcpy.Delete_management(in_data = trend)
    arcpy.Delete_management(in_data = trend_smooth_path)


def main():
    # Call the DetrendDEM function with command line parameters
    DetrendDEM(feature_dataset, flowline, flowline_points, dem, buffer_distance)

if __name__ == "__main__":
    # Get input parameters
    feature_dataset  = _argv(0)
    flowline         = _argv(1)
    flowline_points  = _argv(2)
    dem              = _argv(3)
    buffer_distance  = _argv(4)

    main()
