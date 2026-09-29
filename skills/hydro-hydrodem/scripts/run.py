# -*- coding: utf-8 -*-
"""
水文 DEM 生成（河槽烧录） —— ArcGIS Pro 版

把裁切线（cutlines）按指定栅格宽度下切烧录进 DEM，得到「水文修正 DEM」，使后续流向与河网提取能沿真实河道走。需要 Spatial Analyst 许可。

参数顺序（按工具原定义）：
  1. output_workspace（output_workspace）
  2. cutlines（cutlines）
  3. dem（dem）
  4. widen_cells（widen_cells）

用法：
    python run.py <output_workspace> <cutlines> <dem> <widen_cells>
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
Script Name:          _02_HydroDEM.py
Description:          Burn cutlines into DEM to create a new hydro modified DEM.
Date:                 05/27/2020

Usage:
This script is based on the Agricultural Conservation Planning Framework (ACPF)
http://northcentralwater.org/acpf/ RepairFlowPaths_ManualCutter.py tool.

This tool assumes that all input datasets are in the same coordinate system.

Parameters:
output_workspace (str)-- Path to the output workspace
cutlines (str)        -- Path to the cutlines feature class
dem (str)             -- Path to the digital elevation model (DEM)
widen_cells (int)     -- Number of cells to widen the cutline by

Outputs:
dem_hydro             -- a hydro modified dem
____________________________________________________________________________"""

import os
import arcpy

def BurnCutlines(output_workspace, cutlines, dem, widen_cells):
    arcpy.CheckOutExtension("Spatial")

    # Determine the resolution of dem (assumes planar coordinate system)
    cellsize = float(arcpy.GetRasterProperties_management(
                                         dem, "CELLSIZEX").getOutput(0))

    # Set environment variables
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = output_workspace
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem
    arcpy.env.cellSize = cellsize
    arcpy.env.compression = "LZ77"
    arcpy.env.outputCoordinateSystem = dem

    # List parameter values
    arcpy.AddMessage("Workspace: {}".format(arcpy.env.workspace))
    arcpy.AddMessage("Cutlines: "
                     "{}".format(arcpy.Describe(cutlines).baseName))
    arcpy.AddMessage("DEM: {}".format(arcpy.Describe(dem).baseName))
    arcpy.AddMessage("widen_cells: {}".format(str(widen_cells)))


    # Create a list of cutline OIDs
    cutlines_desc = arcpy.Describe(cutlines)
    cutlines_oid = cutlines_desc.OIDFieldName

    oidList = []
    with arcpy.da.SearchCursor(cutlines, [cutlines_oid]) as cursor:
        for row in cursor:
            id = row[0]
            oidList.append(id)
    arcpy.AddMessage("Cutline OIDs: {}".format(oidList))

    # Convert cutlines to raster
    cutline_ras = os.path.join(output_workspace, "cutline_ras")
    OID = arcpy.Describe(cutlines).OIDFieldName
    arcpy.PolylineToRaster_conversion(
                       in_features = cutlines,
                       value_field = OID,
                       out_rasterdataset = cutline_ras,
                       cellsize = cellsize)

    # Increase width of each cutline
    if int(widen_cells) > 0:
      arcpy.AddMessage("Expanding cutlines...")
      cutline_ras = arcpy.sa.Expand(cutline_ras, int(widen_cells), oidList)

    # Determine the minimum elevation along each cutline
    arcpy.AddMessage("Calculating minumum elevation for each cutline...")
    cutline_min = arcpy.sa.ZonalStatistics(in_zone_data = cutline_ras,
                                           zone_field = "VALUE",
                                           in_value_raster = dem,
                                           statistics_type = "MINIMUM")

    # Con operation to burn cutline_ext into DEM
    arcpy.AddMessage("Burning cutlines into DEM...")
    dem_hydro = arcpy.sa.Con(arcpy.sa.IsNull(cutline_min),
                             dem,
                             cutline_min)

    # Save dem_hydro to the output_workspace
    dem_hydro_path = os.path.join(output_workspace, "dem_hydro")
    arcpy.CopyRaster_management(in_raster = dem_hydro,
                                out_rasterdataset = dem_hydro_path)
    arcpy.AddMessage("Saved hydro modified DEM.")

    # Calculate raster statistics and build pyramids
    arcpy.CalculateStatistics_management(dem_hydro_path)
    arcpy.BuildPyramids_management(dem_hydro_path)
    arcpy.AddMessage("Calculated raster statistics and pyramids.")

    # Return
    arcpy.SetParameter(4, dem_hydro_path)

    # Cleanup
    arcpy.Delete_management(in_data = cutline_ras)


def main():
    # Call the BurnCutlines function with command line parameters
    BurnCutlines(output_workspace, cutlines, dem, widen_cells)

if __name__ == "__main__":
    # Get input parameters
    output_workspace = _argv(0)
    cutlines         = _argv(1)
    dem              = _argv(2)
    widen_cells      = _argv(3)

    main()
