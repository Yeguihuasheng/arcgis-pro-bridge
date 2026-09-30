# -*- coding: utf-8 -*-
"""
2D 点转 3D 点 —— ArcGIS Pro 版

依据 DEM 或指定高程字段把 2D 点要素升级为带 Z 值的 3D 点，用于三维场景布点、高程赋立体。

参数顺序（按工具原定义）：
  1. in_point（in_point）
  2. out_point（out_point）
  3. z_field（z_field）

用法：
    python run.py <in_point> <out_point> <z_field>
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


#coding:utf-8
"""
-------------------------------------------------------------------------------
 Name:        2dto3d_point.py
 Purpose:     2D ポイントの属性値から3D ポイントに変換
 Created:     30/09/2015
-------------------------------------------------------------------------------
"""

import arcpy

# 指定フィールドのインデックスを取得する関数
def get_fieldindex(in_data,target_field):

    fields = arcpy.ListFields(in_data)
    index = [fields.index(field)
                for field in fields if field.name == target_field][0]
    return index

def convert_2dto3d():

    # 変数へ代入
    in_point = _argv(0)
    out_point = _argv(1)
    z_field = _argv(2)

    # z 値を持ったフィーチャクラスを作成
    arcpy.env.outputZFlag = "Enabled"
    arcpy.CopyFeatures_management(in_point,out_point)

    # インデックス取得
    index =  get_fieldindex(in_point,z_field)

    # 出力フィーチャクラスに適した高さフィールドの名称を取得
    output_fields = arcpy.ListFields(out_point)
    update_field = output_fields[index].name

    with arcpy.da.UpdateCursor(out_point,["SHAPE@",update_field]) as up_cur:
        for row in up_cur:
            geom = row[0]
            z_point = arcpy.Point(geom.firstPoint.X,geom.firstPoint.Y,row[1])
            up_cur.updateRow([z_point,row[1]])

    del up_cur


if __name__ == "__main__":
    convert_2dto3d()
