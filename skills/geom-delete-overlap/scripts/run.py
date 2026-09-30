# -*- coding: utf-8 -*-
"""
删除面重叠区域 —— ArcGIS Pro 版

把两组面要素相互重叠的部分从第一组里扣掉，输出不重叠的面，用于清理图斑压盖、双图层去重。

参数顺序（按工具原定义）：
  1. in_poly_fc1（in_poly_fc1）
  2. in_poly_fc2（in_poly_fc2）
  3. out_poly_fc（out_poly_fc）

用法：
    python run.py <in_poly_fc1> <in_poly_fc2> <out_poly_fc>
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
Tool name : ポリゴン同士重なる領域を削除
Source    : DelOverlapPoly.py
Created   : 2019/6/21
Updated   :
"""

class AlreadyExistError(Exception):
    pass


import arcpy
import sys
import os


def setup_del_overlap_poly():
    """
    メソッド名 : setup_del_overlap_poly メソッド
    概要       : ポリゴン同士重なる領域を削除に用いる入力情報の作成
    """
    in_poly_fc1 = _argv(0)
    in_poly_fc2 = _argv(1)
    out_poly_fc = _argv(2)

    del_overlap_poly(in_poly_fc1, in_poly_fc2, out_poly_fc)


def del_overlap_poly(in_poly_fc1, in_poly_fc2, out_poly_fc):
    """
    メソッド名 : del_overlap_poly メソッド
    引数 1     : 入力フィーチャ
    引数 2     : 参照ポリゴンフィーチャ
    引数 3     : 出力フィーチャ
    概要       : ポリゴンの重なる領域を削除
    """
    try:
        arcpy.AddMessage(u"処理開始：")
        in_fc_name = os.path.basename(in_poly_fc1)
        in_ws = os.path.dirname(in_poly_fc1)
        out_fc_name = os.path.basename(out_poly_fc)
        out_ws = os.path.dirname(out_poly_fc)

        # 出力データの作成
        arcpy.CopyFeatures_management(in_poly_fc1, out_poly_fc)

        # ディゾルブ
        arcpy.Dissolve_management(in_poly_fc2, r"memory/dissolve")

        polygons = [row[0] for row in arcpy.da.SearchCursor(r"memory/dissolve", "SHAPE@")]
        outcur = arcpy.da.UpdateCursor(out_poly_fc, "SHAPE@")

        for inrow in outcur:
            for polygon in polygons:
                # ポリゴンが重なっていたら重なる部分を削除
                if inrow[0].overlaps(polygon):
                    outcur.updateRow([inrow[0].difference(polygon)])
                else:
                    pass

        # 後始末
        del outcur

        arcpy.AddMessage(u"処理終了：")
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


if __name__ == u'__main__':
    setup_del_overlap_poly()
