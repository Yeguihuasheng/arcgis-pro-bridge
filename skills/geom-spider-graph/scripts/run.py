# -*- coding: utf-8 -*-
"""
生成辐射连线图 —— ArcGIS Pro 版

由一组源点连到最近的参照点生成直线（蜘蛛图/期望线），输出线要素，常用于设施服务范围、OD 连线可视化。

参数顺序（按工具原定义）：
  1. IN_PT_FC（IN_PT_FC）
  2. REF_PT_FC（REF_PT_FC）
  3. OUT_LINE_FC（OUT_LINE_FC）

用法：
    python run.py <IN_PT_FC> <REF_PT_FC> <OUT_LINE_FC>
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
Tool name : スパイダーグラフの作成
Source    : SpiderGraph.py
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


#スパイダーグラフに用いる入力情報の作成

IN_PT_FC = _argv(0)
REF_PT_FC = _argv(1)
OUT_LINE_FC = _argv(2)
LIMIT = 10000

def check():

    # 同一のフィーチャクラス名がないかチェック
    if arcpy.Exists(OUT_LINE_FC):
        raise AlreadyExistError

    # 入力ポイントの数が10000件以上の場合メッセージを出す
    count = int(arcpy.GetCount_management(IN_PT_FC).getOutput(0))
    if count > LIMIT:
        raise FeatureCountError

    return count

def spider_graph():
    """
    メソッド名： spider_graph メソッド
    引数 1    : 入力ポイント
    引数 2    : 参照ポイント
    引数 4    : 出力フィーチャクラス
    概要　　　： スパイダーグラフの作成
    """
    try:
        arcpy.AddMessage("処理開始：")

        # 同一フィーチャクラス名、入力フィーチャ数のチェック
        count = check()

        # 出力フィーチャクラスの作成
        arcpy.CreateFeatureclass_management(os.path.dirname(OUT_LINE_FC), os.path.basename(OUT_LINE_FC), "POLYLINE", "", "", "", arcpy.Describe(IN_PT_FC).spatialReference)

        # 入力ポイントのOIDを始点ID、参照ポイントのOIDを終点IDとしてフィールドの追加
        arcpy.AddField_management(OUT_LINE_FC, "始点ID" , "LONG")
        arcpy.AddField_management(OUT_LINE_FC, "終点ID" , "LONG")

        # スパイダーグラフの作成
        with arcpy.da.InsertCursor(OUT_LINE_FC, ["SHAPE@", "始点ID", "終点ID"]) as outcur:
            with arcpy.da.SearchCursor(IN_PT_FC, ["OID@", "SHAPE@"]) as incur:
                # 入力ポイント分繰り返し
                for n, inrow in enumerate(incur, start=1):
                    arcpy.AddMessage("{0}/{1}の処理中・・・".format(n, count))

                    with arcpy.da.SearchCursor(REF_PT_FC, ["OID@","SHAPE@"]) as refcur:
                        newvalue_list = None
                        # 参照ポイント分繰り返し
                        for refrow in refcur:
                            #入力と参照ポイントの距離
                            distance = inrow[-1].distanceTo(refrow[-1])

                            # newvalue_list に値が入っていない、または距離が小さい場合に値を格納
                            if newvalue_list is None or distance < newvalue_list[-1]:
                                newvalue_list = [inrow, refrow, distance]

                        # 出力するラインがない(参照ポイントが空)場合、処理終了
                        if newvalue_list == None:
                            break
                        # 入力ポイントと参照ポイントの距離が０でない場合、ラインを作成
                        elif newvalue_list[-1] != 0:
                            in_point = newvalue_list[0][-1].centroid
                            ref_point = newvalue_list[1][-1].centroid
                            out_line = arcpy.Polyline(arcpy.Array([in_point, ref_point]))
                            # 作成したラインと入力ポイント・参照ポイントのOIDを出力
                            outcur.insertRow((out_line, newvalue_list[0][0], newvalue_list[1][0]))


        arcpy.AddMessage("処理終了：")
    except AlreadyExistError:
        arcpy.AddError("{0}はすでに存在しています".format(OUT_LINE_FC))
    except FeatureCountError:
        arcpy.AddError("処理の対象件数が上限{0}件を超えています。".format(LIMIT))
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


if __name__ == u'__main__':
    spider_graph()