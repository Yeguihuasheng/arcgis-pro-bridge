# -*- coding: utf-8 -*-
"""
生成凸包 —— ArcGIS Pro 版

按分组字段为点要素生成凸包（可再按指定距离外扩成缓冲区），输出面要素，常用于求点群的外围轮廓与最小包络范围。

参数顺序（按工具原定义）：
  1. in_pt_fc（in_pt_fc）
  2. out_pt_fc（out_pt_fc）
  3. group_field（group_field）
  4. group_field_name（group_field_name）
  5. create_buffer（create_buffer）
  6. buffer_num（buffer_num）

用法：
    python run.py <in_pt_fc> <out_pt_fc> <group_field> <group_field_name> <create_buffer> <buffer_num>
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
Tool name : 凸包の作成
Source    : CreateConvexhull.py
Created   : 2018/12/14
Updated   :
"""

class AlreadyExistError(Exception):
    pass

import arcpy
import sys
import os


def setup_create_convexhull():
    """
    メソッド名 : setup_create_convexhull メソッド
    概要       : 凸包作成に用いる入力情報の作成
    """
    in_pt_fc = _argv(0)
    out_pt_fc = _argv(1)
    group_field = _gp(2)
    group_field_name = _argv(3)
    create_buffer = _gp(4)
    buffer_num = _gp(5)

    create_convexhull(in_pt_fc, out_pt_fc, group_field, group_field_name, create_buffer, buffer_num)


def create_convexhull(in_pt_fc, out_pt_fc, group_field, group_field_name, create_buffer, buffer_num):
    """
    メソッド名 : create_convexhull メソッド
    引数 1     : 入力フィーチャ
    引数 2     : 出力フィーチャ
    引数 3     : グループ化のフィールド名
    引数 4     : バッファーの距離
    概要       : ポイントを包含する凸包の作成
    """
    try:
        arcpy.AddMessage(u"処理開始：")
        in_fc_name = os.path.basename(in_pt_fc)  # 入力フィーチャクラス(ポイント)名
        in_ws = os.path.dirname(in_pt_fc)  # 入力データのパス
        out_fc_name = os.path.basename(out_pt_fc)  # 出力フィーチャクラス名
        out_ws = os.path.dirname(out_pt_fc)  # 入力データのパス
        # ポリゴンから座標系を取得
        spref = arcpy.Describe(in_pt_fc).spatialReference

        # ワークスペース
        arcpy.env.workspace = out_ws

        # ワークスペースにすでに同一のフィーチャクラス名がないかチェック
        if arcpy.Exists(out_pt_fc):
            raise AlreadyExistError

        tmppoly = "in_memory/tmppoly"
        outdir = os.path.dirname(tmppoly)
        outname = os.path.basename(tmppoly)

        # ポリゴンをテンプレートにしてポイントフィーチャクラスを作成し出力ポイントフィーチャクラスから抽出するフィールドのリストを作成
        arcpy.CreateFeatureclass_management(outdir, outname, u"POLYGON", in_pt_fc, u"DISABLED", u"DISABLED", spref)

        # ディゾルブ
        if group_field == True:
            multipoint = arcpy.Dissolve_management(in_pt_fc, "in_memory/multipoint", group_field_name)
        else:
            multipoint = arcpy.Dissolve_management(in_pt_fc, "in_memory/multipoint")

        fieldlist = []
        fieldlist.append(u'SHAPE@')
        fields = arcpy.Describe(multipoint).fields

        for field in fields:
            if (field.type != u"OID") and (field.type != u"Geometry"):
                fieldlist.append(field.basename)

        # フィーチャクラスの検索カーソル作成
        incur = arcpy.da.SearchCursor(multipoint, fieldlist)
        # フィーチャクラスの挿入カーソル作成
        outcur = arcpy.da.InsertCursor(tmppoly, fieldlist)

        # 処理件数表示用の変数
        i = 0
        num = int(arcpy.GetCount_management(multipoint).getOutput(0))

        for inrow in incur:
            i = i + 1
            if (i == 1) or (i == num) or (i % 1000 == 1):
                s = u"{0}/{1}の処理中・・・".format(i, num)
                arcpy.AddMessage(s)

            if inrow[0].pointCount < 3:
                pass

            copyrow = list(inrow)
            copyrow[0] = inrow[0].convexHull()
            outcur.insertRow(tuple(copyrow))

        # バッファ
        if create_buffer == True:
            arcpy.Buffer_analysis(tmppoly, out_pt_fc, buffer_num)
        else:
            arcpy.CopyFeatures_management(tmppoly, out_pt_fc)

        arcpy.Delete_management("in_memory")

        # 後始末
        del outcur
        del incur

        arcpy.AddMessage(u"処理終了：")
    except AlreadyExistError:
        arcpy.AddError(u"{0}に{1}はすでに存在しています".format(out_ws, out_fc_name))
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


if __name__ == u'__main__':
    setup_create_convexhull()
