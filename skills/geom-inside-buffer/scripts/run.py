# -*- coding: utf-8 -*-
"""
内侧缓冲 —— ArcGIS Pro 版

对面要素做向内收缩的缓冲（负缓冲），得到只包含内部区域的面；与向外扩的退距/管控范围相反，常用于求地块内部可用范围、退缩线。

参数顺序（按工具原定义）：
  1. in_poly_fc（in_poly_fc）
  2. out_poly_fc（out_poly_fc）
  3. buffer_distace（buffer_distace）

用法：
    python run.py <in_poly_fc> <out_poly_fc> <buffer_distace>
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
Tool name : 内向きバッファーの作成
Source    : CreateInsideBuffer.py
Created   : 2018/12/14
Updated   :
"""

class AlreadyExistError(Exception):
    pass


import arcpy
import sys
import os


def setup_create_inside_buffer():
    """
    メソッド名 : setup_create_inside_buffer メソッド
    概要       : バッファー作成に用いる入力情報の作成
    """
    in_poly_fc = _argv(0)
    out_poly_fc = _argv(1)
    buffer_distace = _gp(2)

    create_inside_buffer(in_poly_fc, out_poly_fc, buffer_distace)


def create_inside_buffer(in_poly_fc, out_poly_fc, buffer_distace):
    """
    メソッド名 : create_inside_buffer メソッド
    引数 1     : 入力フィーチャ
    引数 2     : 出力フィーチャ
    引数 3     : バッファーの距離
    概要       : 内向きバッファーの作成
    """
    try:
        arcpy.AddMessage(u"処理開始：")
        in_fc_name = os.path.basename(in_poly_fc)
        in_ws = os.path.dirname(in_poly_fc)
        out_fc_name = os.path.basename(out_poly_fc)
        out_ws = os.path.dirname(out_poly_fc)

        # 出力データの作成
        arcpy.CopyFeatures_management(in_poly_fc,out_poly_fc)

        outcur = arcpy.da.UpdateCursor(out_poly_fc,["SHAPE@"])

        i = 0
        num = int(arcpy.GetCount_management(out_poly_fc).getOutput(0))
        ngcnt = 0

        # バッファ作成
        for inrow in outcur:
            i = i + 1
            if (i == 1) or (i == num) or (i % 1000 == 1):
                s = u"{0}/{1}の処理中・・・".format(i, num)
                arcpy.AddMessage(s)

            inbuffer = inrow[0].buffer(float(buffer_distace) * -1)
            if inbuffer.area == 0.0:
                ngcnt += 1
            else:
                outcur.updateRow([inrow[0].difference(inbuffer)])

        if ngcnt != 0:
            arcpy.AddWarning("内向きバッファのサイズが元のポリゴンの範囲を超えていたため、作成できなかったデータがあります")

        # 後始末
        del outcur

        arcpy.AddMessage(u"処理終了：")

    except AlreadyExistError:
        arcpy.AddError(u"{0}に{1}はすでに存在しています".format(out_ws, out_fc_name))
    except arcpy.ExecuteError:
        # print arcpy.GetMessages(2)
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        # print e.args[0]
        arcpy.AddError(e.args[0])


if __name__ == u'__main__':
    setup_create_inside_buffer()
