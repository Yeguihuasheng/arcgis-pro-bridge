# -*- coding: utf-8 -*-
"""
文件写入 BLOB 字段 —— ArcGIS Pro 版

通过表连接把文件名与要素 ID 关联，再把对应文件读入要素类的 BLOB 字段，完成后清理连接字段，用于把外业照片回挂到要素上。

参数顺序（按工具原定义）：
  1. outFeatureClass（outFeatureClass）
  2. in_field（in_field）
  3. join_table（join_table）
  4. join_field（join_field）
  5. inFieldName（inFieldName）
  6. inFolder（inFolder）
  7. outFieldName（outFieldName）

用法：
    python run.py <outFeatureClass> <in_field> <join_table> <join_field> <inFieldName> <inFolder> <outFieldName>
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
FiletoBLOB.py
Performs a table join to associate image filenames with feature IDs, then reads
the corresponding files from a local directory and inserts them directly into
a BLOB field within the feature class. Cleans up the joined fields upon completion.

Dependencies: arcpy
"""
import arcpy
def script_tool(outFeatureClass, inFolder, inFieldName, outFieldName):
    inFields = []
    inFields.append(inFieldName)
    inFields.append(outFieldName)
    #print(inFields)
    features = arcpy.da.UpdateCursor(outFeatureClass,inFields)
    for feature in features:
        #print(feature[0])
        inRaster = str(inFolder) + "\\" + feature[0]
        #print(inRaster)
        with open(inRaster, "rb") as f:
            #print(f.read())
            feature[1] = f.read()
            features.updateRow(feature)
    return
if __name__ == "__main__":
    # Set the feature class has BLOB field
    outFeatureClass = _argv(0)
    # Set the ID field in outFeatureClass
    in_field = _argv(1)
    # Set the join table has ID-filename relationship
    join_table = _argv(2)
    # Set the ID field in join table
    join_field = _argv(3)
    # Set the name of the field that has image filename.
    inFieldName = _argv(4)
    # Set the photo directory
    inFolder = _argv(5)
    # Set the field name that will store the image BLOB.
    outFieldName = _argv(6)

    arcpy.management.JoinField(outFeatureClass,in_field,join_table,join_field,inFieldName)
    script_tool(outFeatureClass, inFolder, inFieldName, outFieldName)
    arcpy.DeleteField_management(outFeatureClass, inFieldName, "DELETE_FIELDS")
    #arcpy.SetParameterAsText(4, "Result")

