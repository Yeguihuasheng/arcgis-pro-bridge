# -*- coding: utf-8 -*-
"""
数据集范围转面 —— ArcGIS Pro 版

把工作空间内每个数据集的范围（extent）生成矩形面，并保留数据集名称，用于快速制作数据覆盖范围索引图。

参数顺序（按工具原定义）：
  1. in_datasets（in_datasets）
  2. out_fc（out_fc）

用法：
    python run.py <in_datasets> <out_fc>
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


import arcpy
import os

def execute(in_datasets, out_fc):
    # use gcs as output sr since all extents will fit in it
    out_sr = arcpy.SpatialReference("WGS 1984")

    in_datasets = in_datasets.split(";")

    arcpy.CreateFeatureclass_management(os.path.dirname(out_fc),
                                        os.path.basename(out_fc),
                                        "POLYGON",
                                        spatial_reference=out_sr)

    arcpy.AddField_management(out_fc, "dataset", "TEXT", 400)

    # add each dataset's extent & the dataset's name to the output
    with arcpy.da.InsertCursor(out_fc, ("SHAPE@", "dataset")) as cur:

        for i in in_datasets:
            d = arcpy.Describe(i)
            ex = d.Extent
            pts = arcpy.Array([arcpy.Point(ex.XMin, ex.YMin),
                              arcpy.Point(ex.XMin, ex.YMax),
                              arcpy.Point(ex.XMax, ex.YMax),
                              arcpy.Point(ex.XMax, ex.YMin),
                              arcpy.Point(ex.XMin, ex.YMin),])

            geom = arcpy.Polygon(pts,  d.SpatialReference)

            if d.SpatialReference != out_sr:
                geom = geom.projectAs(out_sr)
            cur.insertRow([geom, d.CatalogPath])


if __name__ == "__main__":
    execute(_argv(0), _argv(1))
