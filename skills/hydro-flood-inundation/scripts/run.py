# -*- coding: utf-8 -*-
"""
洪水淹没范围分析 —— ArcGIS Pro 版

按给定点位与水位字段在 DEM 上推算洪水淹没范围并输出淹没区，用于洪涝风险评估、淹没示意。

参数顺序（按工具原定义）：
  1. in_table_main（in_table_main）
  2. clip_dem_ft（clip_dem_ft）
  3. output_folder（output_folder）
  4. Inundation_Field（Inundation_Field）
  5. scratchWorkspace（scratchWorkspace）

用法：
    python run.py <in_table_main> <clip_dem_ft> <output_folder> <Inundation_Field> <scratchWorkspace>
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


"""


Create Date: Fri Sep 11 14:54:03 2019

Notice: Calculate Flood Inundation from DEM and Point Location

"""
# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
import arcpy
from sys import argv
import os


in_table_main = _argv(0)
clip_dem_ft = _argv(1)
output_folder = _argv(2)

Inundation_Field = _argv(3)

arcpy.env.scratchWorkspace = _argv(4)


arcpy.env.overwriteOutput = True

arcpy.MakeFeatureLayer_management(in_table_main,"working_lyr")



def Model1():
    with arcpy.da.SearchCursor("working_lyr",[Inundation_Field,"ModelNode","OBJECTID"]) as cursor:
        for item in cursor:
##            if item[2] != 999:
##                arcpy.AddMessage("Skipping where {0} = {1}".format("OBJECTID",item[2]))
##                continue

            arcpy.AddMessage("working on ModelNode {0} , where {1} = {2}".format(item[1],Inundation_Field,item[0]))

            whereClause = "{0} = {1}".format("OBJECTID",item[2])
            arcpy.AddMessage("Selecting Feature with  {0}".format(whereClause))
            arcpy.SelectLayerByAttribute_management("working_lyr", 'NEW_SELECTION',whereClause)


            in_table = arcpy.env.scratchWorkspace + os.path.sep +"Selection_{0}".format(item[1])

            arcpy.CopyFeatures_management("working_lyr", in_table)

            arcpy.AddMessage("Processing Buffer")
            New_Buffer = arcpy.env.scratchWorkspace + os.path.sep +   "New_Buffer_{0}".format(item[1])
            arcpy.Buffer_analysis(in_features=in_table, out_feature_class=New_Buffer, buffer_distance_or_field="1000 Feet", line_side="FULL", line_end_type="ROUND", dissolve_option="NONE", dissolve_field=[], method="PLANAR")
            arcpy.AddMessage(New_Buffer)


            arcpy.AddMessage("Process Contours")
            ContourVal = arcpy.env.scratchWorkspace + os.path.sep + "ContourVal_{0}".format(item[1])
            arcpy.AddMessage(ContourVal)
            arcpy.gp.Contour_sa(clip_dem_ft, ContourVal, 1000000, item[0], 1, "CONTOUR", None)

            Name_Contour_FeatureToPolygo = arcpy.env.scratchWorkspace + os.path.sep + "Name_Contour_FeatureToPolygo_{0}".format(item[1])
            arcpy.AddMessage("Feature to Polygon")
            arcpy.FeatureToPolygon_management([ContourVal], Name_Contour_FeatureToPolygo, "", "ATTRIBUTES", "")

            arcpy.AddMessage("Select Feature By Location")
            Name_Contour_FeatureToPolygo_2_, Output_Layer_Names, Count = arcpy.SelectLayerByLocation_management([Name_Contour_FeatureToPolygo], "INTERSECT", in_table, "", "NEW_SELECTION", "NOT_INVERT")

            arcpy.AddMessage("Writing output Feature Class")
            arcpy.FeatureClassToFeatureClass_conversion(Name_Contour_FeatureToPolygo_2_, output_folder, "{0}_Output".format(item[1]), "")

            arcpy.AddMessage("Deleting Temporary Files")

            arcpy.Delete_management(New_Buffer)
            arcpy.Delete_management(Name_Contour_FeatureToPolygo)
            arcpy.Delete_management(Name_Contour_FeatureToPolygo_2_)

            arcpy.AddMessage("-------------------------\n")







if __name__ == '__main__':
    # Global Environment settings
    Model1()
