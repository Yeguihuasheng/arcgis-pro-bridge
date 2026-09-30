# -*- coding: utf-8 -*-
"""
多环缓冲（含负缓冲） —— ArcGIS Pro 版

按一组逗号分隔的距离（支持负值=向内）生成多环缓冲，并把缓冲距离写进属性字段后合并成一个面要素类；适合做由近及远的圈层分析。

参数顺序（按工具原定义）：
  1. in_fc（in_fc）
  2. wspace（wspace）
  3. out_fc（out_fc）
  4. distances（distances）
  5. dissolveFields（dissolveFields）

用法：
    python run.py <in_fc> <wspace> <out_fc> <distances> <dissolveFields>
"""

import os
import sys

import arcpy


# ---- 生成器补充的运行期兜底（不影响原逻辑）----
# 上游脚本的中间结果常放在 in_memory，重复运行会因为重名而失败，
# 打开覆盖输出后再跑就正常了。
try:
    arcpy.env.overwriteOutput = True
except Exception:
    pass
# 上游的错误处理分支里偶有引用未定义的变量（如 out_fc_name / out_ws），
# 一旦走到那里会抛 NameError 把真正的错误掩盖掉，这里给这些名字兜底。
for _n in ("out_fc_name", "out_ws", "out_fc", "fc_name", "out_name"):
    if _n not in globals():
        globals()[_n] = u""
del _n



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


''' multi-ring-buffers.py: Create multiple ring buffers, keeping the specified attributes of parent feature class.

Process:
    - create inside only buffer for each of the specifed buffer widths
    - store buffer width used as an attribute
    - merge all buffers into a single feature class, ensuring largest width first so narrower ones are drawn on top

Usage:
    multi-ring-buffers [feature class]  [workspace]  [output feature class]  [widths list]  [attributes to keep]

    multi-ring-buffers R:\data.gdb\Foobar_ply  X:\maps\buffers.gdb  Foobar_rings   50,-50,-100,-300,-600  NAME,TYPE


The workspace must exist (workspace: a folder, file geodatabase, or feature dataset).

The width and attribute parameters must be comma separated and have no spaces.

Requires Arcgis 10, Arcinfo license level.

(c) 2021 Environment Yukon, <联系方式已移除>
Licensed under the MIT license: http://www.opensource.org/licenses/MIT

Also see http://gis.stackexchange.com/questions/19505/multiple-ring-buffer-with-attributes
'''

import arcpy
from arcpy import env

in_fc = _argv(0)                   # features to buffer
wspace = _argv(1)                # output workspace
out_fc = _argv(2)                 # finished result
distances = _argv(3).split(',')  # list of buffer widths
# parse list of attributes to keep into semi-colon separated as expected by buffer tool
dissolveFields = _argv(4).replace(',',';')

env.workspace = wspace

sideType = "FULL"
endType = "ROUND"
dissolveType = "LIST"

buffered_fcs = []
for distance in distances:
    #buf_fc = arcpy.ValidateTableName('xxx_' + out_fc + distance)
    distance = int(distance)
    # inside or outside buffer
    if distance < 0:
      buf_fc = "in_memory/buf_i{}".format(abs(distance))
    else:
      buf_fc = "in_memory/buf_o{}".format(distance)
    msg = "...buffering {0} into {1} with width {2}".format(in_fc, buf_fc, distance)
    arcpy.AddMessage(msg)
    print(arcpy.GetMessages())

    arcpy.Buffer_analysis(in_fc, buf_fc, distance, sideType, endType, dissolveType, dissolveFields)

    # store buffer width as attribute value
    arcpy.AddField_management(buf_fc, 'Width', "TEXT", "", "", 16)
    arcpy.CalculateField_management(buf_fc, 'Width', distance, "PYTHON")

    buffered_fcs.append(buf_fc)

# arrange buffers from largest to smallest width
# so the draw order is correct after merging
buffered_fcs.sort()
buffered_fcs.reverse()

msg = "...Merging intermediate buffers into {0}".format(out_fc)
arcpy.AddMessage(msg)
print(arcpy.GetMessages())
arcpy.Merge_management(buffered_fcs, out_fc)

# remove temporary intermediate files
msg = "...Removing intermediate files"
arcpy.AddMessage(msg)
print(arcpy.GetMessages())
arcpy.Delete_management("in_memory")

# Catch .shp file if that was output file instead GDB feature class
resultLayer = arcpy.ListFeatureClasses(out_fc + "*")[0]

# Add to the map if being run interactively
try:
    mxd = (_ for _ in ()).throw(RuntimeError('CURRENT disabled: run in bridge mode'))
    df = arcpy.mapping.ListDataFrames(mxd, "*")[0]
    arcpy.mapping.AddLayer(df, arcpy.mapping.Layer(resultLayer))
    del mxd
except Exception as e:
    arcpy.AddWarning(e)
    print(arcpy.GetMessages())

print(arcpy.GetMessages())
