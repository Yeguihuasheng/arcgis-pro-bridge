# -*- coding: utf-8 -*-
"""
线交点转点 —— ArcGIS Pro 版

求线要素之间的交点（共有点）并生成点要素，可设置重复点的处理方式，用于生成路网节点、管线交点。

参数顺序（按工具原定义）：
  1. in_line_fc（in_line_fc）
  2. out_pt_fc（out_pt_fc）
  3. overlap（overlap）

用法：
    python run.py <in_line_fc> <out_pt_fc> <overlap>
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
Tool name : ラインの共有点をポイントへ変換
Source    : LineJunctionPtToPt.py
Created   : 2018/12/14
Updated   :
"""

class AlreadyExistError(Exception):
    pass


import arcpy
import sys
import os


# フィーチャクラスの作成と属性情報コピーの準備
def create_fieldinfo(in_line_fc, out_pt_fc):
    """
    メソッド名 : create_fieldinfo メソッド
    引数 1     : 入力フィーチャ
    引数 2     : 出力フィーチャクラス
    概要       : カーソル作成に用いるフィールド情報を作成
    """
    # 出力パスの取得
    out_ws = os.path.dirname(out_pt_fc)
    out_fc_name = os.path.basename(out_pt_fc)

    # 入力データの情報を取得
    in_fc_name = os.path.basename(in_line_fc)
    in_ws = os.path.dirname(in_line_fc)
    in_desc = arcpy.Describe(in_line_fc)
    in_fields = in_desc.Fields
    # ポリゴンから座標系を取得
    spref = in_desc.spatialReference

    # フィーチャクラスの作成
    arcpy.CreateFeatureclass_management(out_ws, out_fc_name, "POINT", in_line_fc, "", "", spref)

    # 変数定義
    search_fields_name = []
    search_fields_type = []
    del_fields = []
    use_fields = []

    # 属性情報コピーの準備
    for i, field in enumerate(in_fields):
        if (field.type == u"OID") or (field.type == u"Geometry"):
            pass
        # 出力が Shape ファイルの場合は、削除対象
        elif field.name.lower() == "shape_length" or field.name.lower() == "shape_area":
            del_fields.append(i)
        else:
            search_fields_name.append(field.name)
            search_fields_type.append(field.type)
            # 属性情報コピーの対象となるフィールドのインデックス番号を取得
            use_fields.append(i)

    out_fields = arcpy.ListFields(out_pt_fc)

    # 出力がShape ファイルの場合
    if arcpy.Describe(out_ws).workspacetype == "FileSystem":

        # 入力もShape ファイルの場合はスルー。
        # Shape_Length、Shape_Area フィールドは削除
        if arcpy.Describe(in_desc.path).workspacetype != "FileSystem":
            if len(del_fields) != 0:
                del_fields_name = [out_fields[index].name for index in del_fields]
                arcpy.DeleteField_management(out_pt_fc, del_fields_name)

        # 属性情報コピーの対象とするフィールド名のリストを作成
        # （インデックス番号を用いて Shape ファイルで短くなった名前を取得）
        use_fields_name = [out_fields[index].name for index in use_fields]
        use_fields_name.append("SHAPE@")

    # 出力が GDB の場合は、入力データと同じフィールド構造を使用
    else:
        use_fields_name = search_fields_name

    search_fields_name.append("SHAPE@")

    return search_fields_name, search_fields_type, use_fields_name, spref

# 配列から重複した値を取り除く
def GetUniqueList(seq):
    seen = []
    seen2 = []

    for x in seq:
        if x[-1] not in seen:
            seen.append(x[-1])
            seen2.append(x)
    return seen2

def linejunction_point():
    """
    メソッド名 : linejunction_point メソッド
    概要       : ラインの共有点をポイントへ変換
    """
    try:
        arcpy.AddMessage(u"処理開始：")

        in_line_fc = _argv(0)
        out_pt_fc = _argv(1)
        overlap = _gp(2)

        # ワークスペース
        wstype = arcpy.Describe(os.path.dirname(out_pt_fc)).workspacetype

        # ワークスペースにすでに同一のフィーチャクラス名がないかチェック
        if arcpy.Exists(out_pt_fc):
            raise AlreadyExistError

        if (overlap == True):
            # インターセクト
            arcpy.Intersect_analysis(in_line_fc,r"in_memory\Intersect","NO_FID","","POINT")
            arcpy.MultipartToSinglepart_management(r"in_memory\Intersect",out_pt_fc)
        else:

            # カーソル作成に使用するフィールド情報を create_fieldinfo 関数を用いて取得
            search_fields_name, search_fields_type, use_fields_name, spref = create_fieldinfo(in_line_fc, out_pt_fc)

            # インターセクト ツールを実行して交点にポイント発生
            arcpy.Intersect_analysis(in_line_fc,r"in_memory\Intersect","NO_FID","","POINT")
            # インターセクトの結果はマルチパート ポイントで出力されるため、シングルパートに変換
            arcpy.MultipartToSinglepart_management(r"in_memory\Intersect",r"in_memory\Single")

            # フィーチャクラスの検索カーソル作成
            incur = arcpy.da.SearchCursor(r"in_memory\Single", search_fields_name)
            # フィーチャクラスの挿入カーソル作成
            outcur = arcpy.da.InsertCursor(out_pt_fc, use_fields_name)

            # 重複しているポイントを除外する
            uniqueincor = GetUniqueList(incur)

            for inrow in uniqueincor:

                newValue = []
                # 出力がShape ファイルの場合、NULL 値を格納できないため
                # フィールドのタイプに合わせて、空白や 0 を格納する
                if wstype == "FileSystem":
                    for j, value in enumerate(inrow):
                        if value == None:
                            if search_fields_type[j] == "String":
                                newValue.append("")
                            elif search_fields_type[j] in ["Double", "Integer", "Single", "SmallInteger"]:
                                newValue.append(0)
                            else:
                                newValue.append(value)
                        else:
                            newValue.append(value)
                # GDB は NULL 値を格納可能
                else:
                    newValue = list(inrow)

                # リスト内に同一のポイントが存在しないかを確認
                # ジオメトリにラインの頂点のポイントを格納
                newValue[-1] = inrow[-1]
                # リストからタプルに変換してインサート
                outcur.insertRow(tuple(newValue))

            # 後始末
            del outcur
            del incur

        # インメモリ ワークスペースの削除
        arcpy.Delete_management("in_memory")

        arcpy.AddMessage(u"処理終了：")
    except AlreadyExistError:
        arcpy.AddError(u"{0}はすでに存在しています".format(out_pt_fc))
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


if __name__ == "__main__":
    linejunction_point()
