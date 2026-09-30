# -*- coding: utf-8 -*-
"""
元数据精确复制（批量） —— ArcGIS Pro 版

把一个数据集的元数据原样（精确副本，不改写同步信息）复制给多个目标数据集，用于批量补齐成果元数据。

参数顺序（按工具原定义）：
  1. inputMetadata（inputMetadata）
  2. outputFolder（outputFolder）

用法：
    python run.py <inputMetadata> <outputFolder>
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


# import modules
import arcpy
from os import path

inputMetadata = _argv(0)
outputFolder = _argv(1)
datasets = inputMetadata.split(";")


def xmlExport(fc):
    """
    export metadata from feature class and save as xml file
    """
    # arcgis install directory
    dir = arcpy.GetInstallInfo("desktop")["InstallDir"]
    # exact copy xslt transformation
    xslt = dir + "Metadata/Stylesheets/gpTools/exact copy of.xslt"
    # set output directory
    out_dir = outputFolder
    # set arcpy workspace
    arcpy.env.workspace = out_dir
    # set workspace overwrite true
    arcpy.env.overwriteOutput = True
    #assemble output xml file name
    output_xml = path.join(out_dir, path.basename(fc) + ".xml")
    #XSLT transforamtion
    arcpy.XSLTransform_conversion(fc, xslt, output_xml)


counter = 1
# loop datasets
for inputFC in datasets:
    inputFC = inputFC.replace("'", "")
    # set arcpy Describe object from input
    inputdesc = arcpy.Describe(inputFC)
    arcpy.AddMessage("\n## {} of {} : {}".format(counter, len(datasets), inputdesc.baseName))
    # check input data element is in the list
    if inputdesc.dataType in ["FeatureClass", "RasterDataset", "Workspace", "ShapeFile", "FeatureDataset", "Table", "TextFile"]:
        xmlfile = xmlExport(inputFC)
    else:
        arcpy.AddMessage("Input data type not supported.")
        quit()

    counter += 1

arcpy.AddMessage(" ")