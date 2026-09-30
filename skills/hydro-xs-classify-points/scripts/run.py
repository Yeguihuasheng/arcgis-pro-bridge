# -*- coding: utf-8 -*-
"""
横断面点地貌分类 —— ArcGIS Pro 版

按断面点落在主槽多边形还是洪泛区多边形（可设缓冲距离）把横断面测点分类为河道/河漫滩等地貌部位，用于断面形态与水力分区统计。

参数顺序（按工具原定义）：
  1. feature_dataset（feature_dataset）
  2. xs_points（xs_points）
  3. channel_polygon（channel_polygon）
  4. floodplain_polygon（floodplain_polygon）
  5. buffer_distance（buffer_distance）

用法：
    python run.py <feature_dataset> <xs_points> <channel_polygon> <floodplain_polygon> <buffer_distance>
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
Script Name:          _14a_XSPoints_Classify.py
Description:          Classifies cross section points according to the
                      floodplain features into which they occur.
Date:                 04/03/2024

Usage:


Parameters:
feature_dataset       -- Path to the feature dataset
xs_points             -- Path to the xs_points feature class
channel_polygon       -- Path to the channel_polygon feature class
floodplain_polygon    -- Path to the floodplain_polygon feature class
buffer_distance       -- Buffer distance around the channel and floodplain
                         polygon. Use linear units of feature dataset.

Outputs:
<xs_name>_points      -- the input cross section feature class with new
                         classification fields added.

____________________________________________________________________________"""

import os
import arcpy

def XSPointsClassify(feature_dataset, xs_points, channel_polygon,
                     floodplain_polygon, buffer_distance):

    # Set environment variables
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = os.path.dirname(feature_dataset)

    # List parameter values
    arcpy.AddMessage("Workspace: {}".format(arcpy.env.workspace))
    arcpy.AddMessage("xs_points: {}".format(arcpy.Describe(xs_points).baseName))
    arcpy.AddMessage("channel_polygon: {}".format(arcpy.Describe(channel_polygon).baseName))
    arcpy.AddMessage("floodplain_polygon: {}".format(arcpy.Describe(floodplain_polygon).baseName))
    arcpy.AddMessage("buffer distance: {}".format(buffer_distance))

    # Add a field to hold the classification flag fields
    # Check if the field already exists and if not add it
    field_names = [f.name for f in arcpy.ListFields(xs_points)]
    if "channel" not in field_names:
        arcpy.management.AddField(in_table = xs_points,
                                  field_name = "channel",
                                  field_type = "SHORT")

    arcpy.management.CalculateField(in_table = xs_points,
                                    field = "channel",
                                    expression = "0",
                                    expression_type = "PYTHON3")

    field_names = [f.name for f in arcpy.ListFields(xs_points)]
    if "floodplain" not in field_names:
        arcpy.management.AddField(in_table = xs_points,
                                  field_name = "floodplain",
                                  field_type = "SHORT")

    arcpy.management.CalculateField(in_table = xs_points,
                                    field = "floodplain",
                                    expression = "0",
                                    expression_type = "PYTHON3")
    arcpy.AddMessage("Added classification flag fields.")

    # Buffer floodplain and channel polygon features
    arcpy.analysis.Buffer(in_features = channel_polygon,
                          out_feature_class = "channel_polygon_buffer",
                          buffer_distance_or_field = buffer_distance)
    arcpy.analysis.Buffer(in_features = floodplain_polygon,
                          out_feature_class = "floodplain_polygon_buffer",
                          buffer_distance_or_field = buffer_distance)
    arcpy.AddMessage("Floodplain and channel buffered.")

    # Create xs_points feature layer to use for selecting
    arcpy.MakeFeatureLayer_management(xs_points, "xs_points")

    # Select xs_points overlaping floodplain
    arcpy.management.SelectLayerByLocation(in_layer = "xs_points",
                                           overlap_type = "INTERSECT",
                                           select_features = "floodplain_polygon_buffer",
                                           selection_type = "NEW_SELECTION")

    # Set floodplain flag
    arcpy.management.CalculateField(in_table = "xs_points",
                                    field = "floodplain",
                                    expression = "1",
                                    expression_type = "PYTHON3")
    arcpy.AddMessage("xs_points in floodplain set.")

    # Select xs_points overlaping channel
    arcpy.management.SelectLayerByLocation(in_layer = "xs_points",
                                           overlap_type = "INTERSECT",
                                           select_features = "channel_polygon_buffer",
                                           selection_type = "NEW_SELECTION")

    # Set channel flag
    arcpy.management.CalculateField(in_table = "xs_points",
                                    field = "channel",
                                    expression = "1",
                                    expression_type = "PYTHON3")
    arcpy.AddMessage("xs_points in channel set.")

    # Clear layer selection
    arcpy.management.SelectLayerByAttribute(in_layer_or_view = "xs_points",
                                            selection_type = "CLEAR_SELECTION")

    # Return
    arcpy.SetParameter(5, xs_points)

    return

def main():
    XSPointsClassify(feature_dataset, xs_points, channel_polygon,
                     floodplain_polygon, buffer_distance)

if __name__ == "__main__":
    feature_dataset    = _argv(0)
    xs_points          = _argv(1)
    channel_polygon    = _argv(2)
    floodplain_polygon = _argv(3)
    buffer_distance    = _argv(4)

    main()
