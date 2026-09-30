# -*- coding: utf-8 -*-
"""
按参照面分摊面积 —— ArcGIS Pro 版

以另一组面为参照，把源面的指定数值字段按相交面积比例分摊（面积按分），写入输出面，用于指标按占比拆分、跨行政区指标分摊。

参数顺序（按工具原定义）：
  1. IN_POLY_FC（IN_POLY_FC）
  2. REF_POLY_FC（REF_POLY_FC）
  3. 字段（可多选）（FIELDS）
  4. OUT_POLY_FC（OUT_POLY_FC）

用法：
    python run.py <IN_POLY_FC> <REF_POLY_FC> <FIELDS> <OUT_POLY_FC>
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
Tool name : 面積を按分
Source    : ProportionalDivisionArea.py
Created   : 2019/12/26
Updated   :
"""

import sys
import os
import arcpy


class AlreadyExistError(Exception):
    pass

class FeatureCountError(Exception):
    pass


#面積按分に用いる入力情報の作成

IN_POLY_FC = _argv(0)
REF_POLY_FC = _argv(1)
FIELDS = _argv(2)
OUT_POLY_FC = _argv(3)
LIMIT = 10000

def check(out_poly_fc, overlap):

    # 同一のフィーチャクラス名がないかチェック
    if arcpy.Exists(OUT_POLY_FC):
        raise AlreadyExistError

    # 入力ポリゴンの数が10000件以上の場合メッセージを出す
    count = int(arcpy.GetCount_management(overlap).getOutput(0))
    if count > LIMIT:
        raise FeatureCountError

    return count


def create_temporary_data():

    # テンポラリ データの作成
    arcpy.CopyFeatures_management(REF_POLY_FC, r"in_memory\Copy")

    # 選択したフィールド（FIELDS）が"Shape_Area"もしくは"Shape_Length"だった場合メモリ上にフィールドがコピーされないため、新しいフィールド"Area","Length"を追加し、フィールド演算で値を格納
    fields = FIELDS.split(";")
    if "Shape_Area" in fields:
        arcpy.AddField_management(r"in_memory\Copy", "Area", "DOUBLE")
        arcpy.CalculateField_management(r"in_memory\Copy", "Area", "!Shape!.area", "PYTHON3")
    if "Shape_Length" in fields:
        arcpy.AddField_management(r"in_memory\Copy", "Length", "DOUBLE")
        arcpy.CalculateField_management(r"in_memory\Copy", "Length", "!Shape!.length", "PYTHON3")

    arcpy.AddField_management(r"in_memory\Copy", "area", "DOUBLE")
    arcpy.CalculateField_management(r"in_memory\Copy", "area", "!Shape!.area", "PYTHON3")


def proportional_division_area():
    """
    メソッド名：proportional_division_area メソッド
    引数 1    : 入力フィーチャ
    引数 2    : 参照ポリゴン
    引数 3    : フィールド名
    引数 4    : 出力フィーチャ
    概要　　　： 面積を按分
    """
    try:
        arcpy.AddMessage("処理開始：")

        # 空間検索で入力ポリゴンと重なっている参照ポリゴンのフィーチャを選択
        overlap = arcpy.SelectLayerByLocation_management(IN_POLY_FC, "INTERSECT", REF_POLY_FC)
        # 同一フィーチャクラス名、重なるフィーチャ数のチェック
        count = check(OUT_POLY_FC, overlap)
        # テンポラリデータの作成
        create_temporary_data()
        # 出力フィーチャクラスの作成
        arcpy.CreateFeatureclass_management(os.path.dirname(OUT_POLY_FC), os.path.basename(OUT_POLY_FC), "POLYGON", "", "", "", arcpy.Describe(IN_POLY_FC).spatialReference)

        # 入力フィールドが複数の場合フィールドごとに分割しフィールドの追加
        field_list = ["SHAPE@"]

        for field in FIELDS.split(";"):
            if field == "Shape_Area":
                field = "Area"
            elif field == "Shape_Length":
                field = "Length"
            arcpy.AddField_management(OUT_POLY_FC, field, "DOUBLE")
            field_list.append(field)

        field_count = len(FIELDS.split(";"))
        n = 0

        # 面積按分
        with arcpy.da.InsertCursor(OUT_POLY_FC, field_list) as outcur:
            with arcpy.da.SearchCursor(overlap, ["SHAPE@"]) as incur:
                for inrow in incur:
                    n = n + 1
                    arcpy.AddMessage("{0}/{1}の処理中・・・".format(n, count))

                    arcpy.Clip_analysis(r"in_memory\Copy", inrow[0], r"in_memory\Clip")
                    new_value_list = []
                    for i in range(field_count):
                        new_value = 0
                        with arcpy.da.SearchCursor(r"in_memory\Clip", field_list + ["area"]) as clipcur:
                            for cliprow in clipcur:
                                if cliprow[i + 1] == None:
                                    pass
                                else:
                                    new_value += cliprow[i + 1] * cliprow[0].area / cliprow[-1]
                        new_value_list.append(new_value)
                    outcur.insertRow([inrow[0]] + new_value_list)
                    arcpy.Delete_management(r"in_memory\Clip")

        arcpy.Delete_management(r"in_memory\Copy")


        arcpy.AddMessage("処理終了：")
    except AlreadyExistError:
        arcpy.AddError("{0}はすでに存在しています".format(OUT_POLY_FC))
    except FeatureCountError:
        arcpy.AddError(u"処理の対象件数が上限{0}件を超えています。".format(LIMIT))
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


if __name__ == u'__main__':
    proportional_division_area()