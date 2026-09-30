# -*- coding: utf-8 -*-
"""
生成泰森多边形 —— ArcGIS Pro 版

为点要素生成泰森多边形（最近邻分配面），输出面要素，用于服务区划分、站点影响范围。

参数顺序（按工具原定义）：
  1. IN_PT_FC（IN_PT_FC）
  2. OUT_POLY_FC（OUT_POLY_FC）

用法：
    python run.py <IN_PT_FC> <OUT_POLY_FC>
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
Tool name : ティーセンポリゴンの作成
Source    : Thiessen.py
Created   : 2019/12/26
Updated   : 2022/5/20
"""

import sys
import os
import arcpy
from scipy.spatial import Voronoi


class AlreadyExistError(Exception):
    pass

class FeatureCountError(Exception):
    pass


#ティーセンポリゴンに用いる入力情報の作成
IN_PT_FC = _argv(0)
OUT_POLY_FC = _argv(1)
LIMIT = 50000
count = 0

def check():
    """
    概要　　　： 同一の出力フィーチャクラス名がないか、
    　　　　　　 入力ポイントが処理の上限数以上ないかチェックします。
    """

    # 同一のフィーチャクラス名がないかチェック
    if arcpy.Exists(OUT_POLY_FC):
        raise AlreadyExistError

    # 入力ポイントの数が10000件以上の場合メッセージを出す
    global count
    count = int(arcpy.GetCount_management(IN_PT_FC).getOutput(0))
    if count > LIMIT:
        raise FeatureCountError

def create_voronoi(point_list, out):
    """
    概要　　　： ティーセンポリゴンを作成します。
    引数１    : point_list　入力ポイント（IN_PT_FC）の座標のリスト
    引数２    : outcur　ティーセンポリゴンを挿入するカーソルオブジェクト
    """

    # voronoi関数をそのまま実行すると端点にティーセンポリゴンが作成されないため、ティーセンポリゴン作成用ポイントを追加
    x = [x[0] for x in point_list]
    y = [y[1] for y in point_list]

    deltaX = max(x) - min(x)
    deltaY = max(y) - min(y)

    Xmin = min(x) - deltaX
    Ymin = min(y) - deltaY
    Xmax = max(x) + deltaX
    Ymax = max(y) + deltaY

    point_list.append((Xmax, Ymax))
    point_list.append((Xmax, Ymin))
    point_list.append((Xmin, Ymax))
    point_list.append((Xmin, Ymin))

    # ティーセンの作成
    vor = Voronoi(point_list)

    # ティーセンポリゴンの頂点の組み合わせを抽出
    vor_verticies = [r for r in vor.regions if -1 not in r and r]

    with arcpy.da.InsertCursor(out, ["SHAPE@"]) as outcur:
        # 抽出した頂点の組み合わせから頂点の座標を取得してティーセンポリゴンを作成
        for n, region in enumerate(vor_verticies, start=1):
            arcpy.AddMessage("{0}/{1}の処理中・・・".format(n, count))
            coordinates = [vor.vertices[region]]
            coordinates_list = coordinates[0].tolist()
            arcpy.AddMessage(coordinates_list)
            outcur.insertRow([coordinates_list])

    # 作成したボロノイ図を整えるためのクリップする範囲を計算
    Xmin = min(x) - (deltaX / 10)
    Ymin = min(y) - (deltaY / 10)
    Xmax = max(x) + (deltaX / 10)
    Ymax = max(y) + (deltaY / 10)


    # クリップフィーチャの作成
    array = arcpy.Array([arcpy.Point(Xmax, Ymax),
                         arcpy.Point(Xmax, Ymin),
                         arcpy.Point(Xmin, Ymin),
                         arcpy.Point(Xmin, Ymax)])
    clip_poly = arcpy.Polygon(array, spatial_reference=arcpy.Describe(IN_PT_FC).spatialReference)

    # クリップしフィーチャクラスを出力
    arcpy.Clip_analysis(out, clip_poly, OUT_POLY_FC)
    arcpy.Delete_management(out)


def thiessen():
    """
    概要　　　： ティーセンポリゴンの作成に用いる入力ポイントの座標を取得します。
    """
    try:
        arcpy.AddMessage("処理開始：")

        # 同一フィーチャクラス名、入力フィーチャ数のチェック
        check()

        # メモリ上にフィーチャクラス作成
        arcpy.CreateFeatureclass_management("memory", "out", "POLYGON", "", "", "",
                                            arcpy.Describe(IN_PT_FC).spatialReference)
        out = "memory/out"
        point_list = []

        # 入力ポイントのXYをリストに格納
        with arcpy.da.SearchCursor(IN_PT_FC, ["SHAPE@"]) as incur:
            for inrow in incur:
                point_list.append((inrow[0].centroid.X, inrow[0].centroid.Y))

            #入力ポイント数が2件以上のときcreate_voronoiメソッドでティーセンポリゴンの作成、2件以下のときは処理を終了する
            if count >= 2:
                create_voronoi(point_list, out)
                arcpy.AddMessage("処理終了：")
            else:
                arcpy.AddMessage("作成されるティーセンポリゴンは0件のため処理を終了します。")
    except AlreadyExistError:
        arcpy.AddError("{0}はすでに存在しています".format(OUT_POLY_FC))
    except FeatureCountError:
        arcpy.AddError("処理の対象件数が上限{0}件を超えています。".format(LIMIT))
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError("ティーセンポリゴンの作成に失敗しました。")

if __name__ == '__main__':
    thiessen()