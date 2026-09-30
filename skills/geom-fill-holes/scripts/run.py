# -*- coding: utf-8 -*-
"""
填补面内空洞 —— ArcGIS Pro 版

把面要素内部的孔洞（内环）填实，输出无孔的面，用于消除图斑中间被误挖的空白。

参数顺序（按工具原定义）：
  1. in_poly_fc（in_poly_fc）
  2. out_poly_fc（out_poly_fc）

用法：
    python run.py <in_poly_fc> <out_poly_fc>
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


# coding:utf-8
"""
Tool name : ポリゴンを穴埋め
Source    : PolyFillingUp.py
Created   : 2019/6/21
Updated   : 2022/7/13
"""

class AlreadyExistError(Exception):
    pass


import arcpy
import sys
import os


def setup_poly_filling_up():
    """
    メソッド名 : setup_poly_filling_up メソッド
    概要       : ポリゴンの穴埋めに用いる入力情報の作成
    """
    in_poly_fc = _argv(0)
    out_poly_fc = _argv(1)

    poly_filling_up(in_poly_fc, out_poly_fc)


def poly_filling_up(in_poly_fc, out_poly_fc):
    """
    メソッド名 : poly_filling_up メソッド
    引数 1     : 入力フィーチャ
    引数 2     : 出力フィーチャ
    概要       : ポリゴンを穴埋め
    """
    try:
        arcpy.AddMessage(u"処理開始：")
        in_fc_name = os.path.basename(in_poly_fc)
        in_ws = os.path.dirname(in_poly_fc)
        out_fc_name = os.path.basename(out_poly_fc)
        out_ws = os.path.dirname(out_poly_fc)
        spatial_ref = arcpy.Describe(in_poly_fc).spatialReference

        # 出力データの作成
        arcpy.CopyFeatures_management(in_poly_fc, out_poly_fc)

        outcur = arcpy.da.UpdateCursor(out_poly_fc, "SHAPE@")

        for inrow in outcur:
            polygon = arcpy.Array()
            for part in inrow[0]:
                new_part = arcpy.Array()
                # Nullになるポイント(interior ring の最初)を取得
                null_point = 0
                i = 0
                for i in range(len(part)):
                    if part[i] == None:
                        null_point = i
                        break
                # 穴あきポリゴンでない場合パートの数そのまま
                if null_point == 0:
                    polygon.add(part)
                # 穴あきポリゴンの場合パートの数をinterior ringの一つ前のポイントまでに
                else:
                    j = 0
                    for j in range(null_point):
                        new_part.add(part[j])
                    polygon.add(new_part)
            if len(polygon) > 0:
                new_poly = arcpy.Polygon(polygon, spatial_ref)
                inrow[0] = new_poly
                outcur.updateRow(inrow)

        # 後始末
        del outcur

        arcpy.AddMessage(u"処理終了：")
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


if __name__ == u'__main__':
    setup_poly_filling_up()
