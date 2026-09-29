# -*- coding: utf-8 -*-
"""
洼地（汇水点）提取 —— ArcGIS Pro 版

对 DEM 做均值邻域统计与填洼后反求洼地位置，再按最小面积过滤、按距离做缓冲合并，输出湿地洼地栅格，用于湿地水文分析找汇水点。

参数顺序（按工具原定义）：
  1. DEMRasterPath（DEMRasterPath）
  2. min_size（min_size）
  3. buff_dis（buff_dis）
  4. outputRaster（outputRaster）

用法：
    python run.py <DEMRasterPath> <min_size> <buff_dis> <outputRaster>
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


__author__ = 'Qiusheng'
import arcpy
import os
from arcpy import env

def PreProcess(DEMRasterPath,min_size,buffer_dist,outPutRaster):
    arcpy.CheckOutExtension("Spatial")
    input_dir = os.path.split(outPutRaster)[0]
    gdb = os.path.split(outPutRaster)[0]

    if os.path.splitext(input_dir)[1].lower() == ".gdb":
        input_dir = os.path.split(input_dir)[0]
        #gdb = os.path.split(outPutRaster)[0]

    env.workspace = input_dir
    env.overwriteOutput = True

    if arcpy.Exists(DEMRasterPath) == False:
        print("The input raster does not exist")
        quit()

    ### Mean Focal Statistics
    ras_mf = arcpy.sa.FocalStatistics(DEMRasterPath,"Rectangle 3 3 CELL","MEAN","DATA")

    ### Fill depression
    ras_fill = arcpy.sa.Fill(ras_mf)
    ras_fill.save(os.path.join(input_dir,"dem_filled.tif"))
    ### Get sink
    ras_sink = ras_fill - ras_mf

    ### Convert foreground sink
    #ras_sink_fg = arcpy.sa.Con(ras_sink,ras_sink,"#",'"Value">0')
    #ras_sink_fg.save("ras_sink_fg")

    ### Convert sink to binary image
    ras_sink_bin = arcpy.sa.Con(ras_sink > 0,1)

    ### Region group
    ras_region = arcpy.sa.RegionGroup(ras_sink_bin,"FOUR","WITHIN","ADD_LINK")

    ### Convert raster to polygon
    region_poly_name = os.path.join(input_dir,"region_poly.shp")
    arcpy.RasterToPolygon_conversion(ras_region,region_poly_name,"NO_SIMPLIFY")

    ### Select polygon based on minimum size
    area_field = "Area"
    arcpy.AddField_management(region_poly_name, area_field, "DOUBLE")
    arcpy.CalculateField_management(region_poly_name,"Area","!shape.area@squaremeters!","PYTHON_9.3","#")
    sqlExp = area_field + ">=" + str(min_size)

    ##print sqlExp
    region_poly_select_name = os.path.join(input_dir,"sink_poly.shp")
    arcpy.Select_analysis(region_poly_name,region_poly_select_name,sqlExp)

    ### Calculate field
    arcpy.CalculateField_management(region_poly_select_name,"gridcode","1","PYTHON")

    #### Convert polygon to raster
    region_poly_ras = os.path.join(input_dir,"region_poly_ras.tif")
    arcpy.PolygonToRaster_conversion(region_poly_select_name,"gridcode",region_poly_ras,"CELL_CENTER","NONE","1")

    ### Convert foreground sink TO 0
    ras_sink_bg = ras_mf - ras_mf
    ras_sink_bg.save(os.path.join(input_dir,"ras_sink_bg.tif"))

    #ras_sink_final = "ras_sink_final"
    in_ras_list = [region_poly_ras,ras_sink_bg]
    ras_sink_final_name = arcpy.sa.CellStatistics(in_ras_list,"SUM","DATA")
    arcpy.env.extent = ras_mf.extent
    ras_sink_final_name = arcpy.sa.ApplyEnvironment(ras_sink_final_name)
    #ras_name.save(os.path.join(input_dir,"ras_name.tif"))
    ### Convert foreground sink
    dem_name = arcpy.sa.Con(ras_sink_final_name==1,ras_mf,ras_fill)
    dem_name = arcpy.sa.ApplyEnvironment(dem_name)
    dem_name.save(os.path.join(input_dir,"dem_final.tif"))

    ### buffer sink area
    sink_buffer_name = os.path.join(input_dir,"sink_buffer.shp")
    sqlExp = str(buffer_dist) + " Meters"
    arcpy.Buffer_analysis(region_poly_select_name,sink_buffer_name,sqlExp,"","","ALL","")

    dem_sink = arcpy.sa.Con(ras_sink_final_name==1,ras_mf,ras_fill)
    dem_sink = arcpy.sa.ExtractByMask(dem_name,sink_buffer_name)
    dem_sink = arcpy.sa.ApplyEnvironment(dem_sink)
    arcpy.CopyRaster_management(dem_sink,outPutRaster)
    #dem_sink.save(outPutRaster)
    #dem_sink.save(os.path.join(input_dir,"sink_buffer.tif"))

    dem_sink_depth = ras_fill - dem_name
    dem_sink_depth_name = arcpy.sa.Con(dem_sink_depth>0,dem_sink)
    dem_sink_depth_name = arcpy.sa.ApplyEnvironment(dem_sink_depth_name)
    dem_sink_depth_name.save(os.path.join(input_dir,"sink_no_buffer.tif"))

    sink_depth = arcpy.sa.Con(dem_sink_depth>0,dem_sink_depth)
    sink_depth = arcpy.sa.ApplyEnvironment(sink_depth)
    sink_depth.save(os.path.join(input_dir,"sink_depth.tif"))

    arcpy.Delete_management(region_poly_name)
    arcpy.Delete_management(region_poly_ras)
    arcpy.Delete_management(sink_buffer_name)
    arcpy.Delete_management(os.path.join(input_dir,"ras_sink_bg.tif"))

    ### These data can be saved when needed.
    ### Save to a geodatabase
    if os.path.splitext(gdb)[1].lower() == ".gdb":
        arcpy.CopyRaster_management(os.path.join(input_dir,"sink_no_buffer.tif"),os.path.join(gdb,"sink_no_buffer"))
        arcpy.CopyRaster_management(os.path.join(input_dir,"dem_final.tif"),os.path.join(gdb,"dem_final"))
        arcpy.CopyRaster_management(os.path.join(input_dir,"sink_depth.tif"),os.path.join(gdb,"sink_depth"))
        arcpy.CopyRaster_management(os.path.join(input_dir,"dem_filled.tif"),os.path.join(gdb,"dem_filled"))
        arcpy.CopyFeatures_management(region_poly_select_name,os.path.join(gdb,"sink_poly"))
        arcpy.Delete_management(region_poly_select_name)
        arcpy.Delete_management(os.path.join(input_dir,"sink_no_buffer.tif"))
        arcpy.Delete_management(os.path.join(input_dir,"dem_final.tif"))
        arcpy.Delete_management(os.path.join(input_dir,"sink_depth.tif"))
        arcpy.Delete_management(os.path.join(input_dir,"dem_filled.tif"))

    #arcpy.Delete_management(region_poly_select_name)
    #arcpy.Delete_management(os.path.join(input_dir,"sink_no_buffer.tif"))
    #arcpy.Delete_management(os.path.join(input_dir,"dem_final.tif"))
    #arcpy.Delete_management(os.path.join(input_dir,"sink_depth.tif"))

    return outPutRaster

    print("PreProcess Done!")
DEMRasterPath = _argv(0)
min_size = float(_argv(1))
buff_dis = float(_argv(2))
outputRaster = _argv(3)
PreProcess(DEMRasterPath,min_size,buff_dis,outputRaster)
