# -*- coding: utf-8 -*-
"""
DEM 剖面提取 —— ArcGIS Pro 版

沿指定线在 DEM 上采样高程并输出剖面表与剖面图，用于地形起伏分析、纵横断面校核。

参数顺序（按工具原定义）：
  1. inputdem（inputdem）
  2. inputlinea（inputlinea）
  3. salidatabla（salidatabla）
  4. salidagraf（salidagraf）

用法：
    python run.py <inputdem> <inputlinea> <salidatabla> <salidagraf>
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


#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
#
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy

inputdem = _argv(0)
inputlinea = _argv(1)
salidatabla = _argv(2)
salidagraf = _argv(3)

if inputdem == '#' or not inputdem:
    inputdem = "DEM"

if inputlinea == '#' or not inputlinea:
    inputlinea = "Linea"

if salidatabla == '#' or not salidatabla:
    salidatabla = ""

nombre_grafico = "Perfil"
if nombre_grafico == '#' or not nombre_grafico:
    nombre_grafico = "Grafica"

if arcpy.CheckExtension('3D') == 'Available':
    arcpy.CheckOutExtension('3D')
    arcpy.StackProfile_3d(inputlinea, inputdem, salidatabla, nombre_grafico)
    arcpy.management.SaveGraph(nombre_grafico, salidagraf)
    arcpy.CheckInExtension('3D')

