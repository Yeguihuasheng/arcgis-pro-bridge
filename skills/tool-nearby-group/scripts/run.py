# -*- coding: utf-8 -*-
"""
邻近要素分组编号 —— ArcGIS Pro 版

按搜索半径找出与目标要素相邻的要素，并把它们归为同一组、写入分组编号字段，用于相邻图斑合并、地块归并、违建图斑聚合等。

参数顺序（按工具原定义）：
  1. in_features（in_features）
  2. group_fields（group_fields）
  3. near_features（near_features）
  4. search_radius（search_radius）

用法：
    python run.py <in_features> <group_fields> <near_features> <search_radius>
"""

import os
import sys

import arcpy


def _argv(i):
    """替代 arcpy.GetParameterAsText(i)：从命令行取第 i 个参数。"""
    if len(sys.argv) > i + 1:
        return sys.argv[i + 1]
    return u""


'''----------------------------------------------------------------------------------
 Tool Name:   Near By Group
 Source Name: nearbygroup.py
 Version:     ArcGIS 10
 Required Arguments:
              Input Features (Feature Layer)
              Group Field(s) (Fields)
              Near Features (Feature Layer)
 Optional Arguments:
              Search Radius (Linear Unit)

 Description: Determines the distance from each feature in the Input Features to
                the nearest feature in the same attribute group.

----------------------------------------------------------------------------------'''

# Import system modules
import arcpy
import os

arcpy.env.overwriteOutput = True

# Main function, all functions run in NearByGroup
def NearByGroup(in_features, group_fields, near_features, search_radius=""):

    if arcpy.ProductInfo().lower() not in ['arcinfo']:
        arcpy.AddError("An ArcGIS for Desktop Advanced license is required.")
        sys.exit()

    # Read field values from input features
    uniq_values = set()
    scur = arcpy.SearchCursor(in_features, "", "", ";".join(group_fields))
    try:
        for row in scur:
            value = tuple()
            for field in group_fields:
                value += (row.getValue(field),)
            uniq_values.add(value)
    except:""
    finally:
        if scur:
            del scur

    # Add fields to Input
    arcpy.management.AddField(in_features, "NEAR_OID", "LONG")
    arcpy.management.AddField(in_features, "NEAR_DISTN", "DOUBLE")
    arcpy.management.AddField(in_features, "NEAR_FCLS", "TEXT")

    # Make a selection based on the values
    arcpy.management.MakeFeatureLayer(in_features, "input_lyr")
    near_features_list = []
    for each in near_features:
        arcpy.management.MakeFeatureLayer(each, "{0}_lyr".format(os.path.splitext(os.path.basename(each))[0]))
        near_features_list.append("{0}_lyr".format(os.path.splitext(os.path.basename(each))[0]))

    # Set the progress bar
    arcpy.SetProgressor("step", "Processing...", 0, len(uniq_values), 1)
    for uniq_value in uniq_values:
        expr = ""
        for combo in zip(uniq_value, group_fields):
            val = "'{0}'".format(combo[0]) if type(combo[0]) == str or type(combo[0]) == unicode else combo[0]
            expr += """{0} = {1} AND """.format(combo[1], val)
        expr = expr[:-5]
        # Select the input features
        arcpy.management.SelectLayerByAttribute("input_lyr", "", expr)
        for each in near_features_list:
            arcpy.management.SelectLayerByAttribute(each, "", expr)

        # Run the Near process
        arcpy.analysis.Near("input_lyr", near_features_list, search_radius)

        # Calculate the values into the NEAR_FID and NEAR_DISTN fields
        arcpy.management.CalculateField("input_lyr", "NEAR_OID", "!NEAR_FID!", "PYTHON")
        arcpy.management.CalculateField("input_lyr", "NEAR_DISTN", "!NEAR_DIST!", "PYTHON")
        if len(near_features) > 1:
            arcpy.management.CalculateField("input_lyr", "NEAR_FCLS", """getpath(!NEAR_FC!)""", "PYTHON", """def getpath(layer):\n    try:\n        return arcpy.Describe(str(layer)).catalogPath\n    except:\n        return 'None'""")
        else:
            arcpy.management.CalculateField("input_lyr", "NEAR_FCLS", """r'{0}'""".format(arcpy.Describe(near_features[0]).catalogPath), "PYTHON")
        arcpy.SetProgressorPosition()

    # Clean up
    arcpy.management.DeleteField("input_lyr", "NEAR_FID;NEAR_DIST;NEAR_FC")
    for each in ["input_lyr"] + near_features_list:
        try:
            arcpy.management.Delete(each)
        except:
            ""

# Run the script
if __name__ == '__main__':
    in_features = _argv(0)
    group_fields = _argv(1).split(";") if _argv(1).find(";") > -1 else [_argv(1)]
    near_features = _argv(2).split(";") if _argv(2).find(";") > -1 else [_argv(2)]
    search_radius = _argv(3)

    NearByGroup(in_features, group_fields, near_features, search_radius)
    arcpy.SetParameterAsText(4, in_features)
    print ("finished")