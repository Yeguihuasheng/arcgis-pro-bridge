# -*- coding: utf-8 -*-
"""
D8 流向与汇流累积计算 —— ArcGIS Pro 版

由水文修正 DEM 计算 D8 流向栅格与汇流累积（汇水面积）栅格；ESRI 分水岭工具要求 D8 流向，因此本技能通常作为「按点划定流域」的前置步骤。

参数顺序（按工具原定义）：
  1. output_workspace（output_workspace）
  2. dem_hydro（dem_hydro）
  3. processes（processes）

用法：
    python run.py <output_workspace> <dem_hydro> <processes>
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
Script Name:          _03a_ContributingAreaD8.py
Description:          Calculates D8 flow accumulation and flow direction
                      rasters from an input DEM.
Date:                 05/14/2020

Usage:
This tool calculates Flow Direction and Flow Accumulation using the D8 method
from a hydro modified digital elevation model (DEM).

The ESRI Watershed tool requires a flow direction raster to be calculated using
the D8 method. Therefore, this tool is intentended to be used prior to the
FluvialGeomorph Point Watershed tool.

Parameters:
output_workspace      -- Path to the output workspace.
dem_hydro             -- Path to the hydro modified digital elevation model (DEM).
processes             -- The number of processes to use for parallel processing.

Outputs:
flow_direction_D8     -- A flow direction raster using the D8 method (integer
                         flow directions).
____________________________________________________________________________"""

import os
import arcpy
from arcpy.sa import *

def StudyAreaWatershed(output_workspace, dem_hydro, processes):
    arcpy.CheckOutExtension("Spatial")

    # Set environment variables
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = output_workspace
    arcpy.env.scratchWorkspace = output_workspace
    arcpy.env.cellSize = dem_hydro
    arcpy.env.parallelProcessingFactor = processes

    # List parameter values
    arcpy.AddMessage("Workspace: {}".format(arcpy.env.workspace))
    arcpy.AddMessage("DEM hydro: "
                     "{}".format(arcpy.Describe(dem_hydro).baseName))
    arcpy.AddMessage("processes: {}".format(processes))

    # Fill sinks
    arcpy.AddMessage("Beginning filling sinks...")
    dem_fill = arcpy.sa.Fill(in_surface_raster = dem_hydro)
    arcpy.AddMessage("Fill sinks complete.")

    # Calculate D8 flow direction (suitable for input into the Watershed tool)
    arcpy.AddMessage("Beginning flow direction...")
    flow_dir_d8 = arcpy.sa.FlowDirection(in_surface_raster = dem_fill,
                                         flow_direction_type = "D8")
    flow_direction_d8 = os.path.join(output_workspace, "flow_direction_d8")
    flow_dir_d8.save(flow_direction_d8)

    # Calculate raster statistics and build pyramids
    arcpy.AddMessage("    Calculating statistics...")
    arcpy.CalculateStatistics_management(flow_direction_d8)
    arcpy.AddMessage("    Building pyraminds...")
    arcpy.BuildPyramids_management(flow_direction_d8)
    arcpy.AddMessage("Flow direction complete.")

    # Calculate flow accumulation
    arcpy.AddMessage("Beginning flow accumulation...")
    flow_accum_d8 = arcpy.sa.FlowAccumulation(flow_dir_d8,
                                              data_type = "FLOAT",
                                              flow_direction_type = "D8")
    flow_accumulation_d8 = os.path.join(output_workspace, "flow_accumulation_d8")
    flow_accum_d8.save(flow_accumulation_d8)

    # Calculate raster statistics and build pyramids
    arcpy.AddMessage("    Calculating statistics...")
    arcpy.CalculateStatistics_management(flow_accumulation_d8)
    arcpy.AddMessage("    Building pyraminds...")
    arcpy.BuildPyramids_management(flow_accumulation_d8)
    arcpy.AddMessage("Flow accumulation complete.")

    # Return
    arcpy.SetParameter(3, flow_accumulation_d8)

def main():
    # Call the StudyAreaWatershed function with command line parameters
    StudyAreaWatershed(output_workspace, dem_hydro, processes)

if __name__ == "__main__":
    # Get input parameters
    output_workspace = _argv(0)
    dem_hydro        = _argv(1)
    processes        = _argv(2)

    main()

