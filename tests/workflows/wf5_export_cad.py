# -*- coding: utf-8 -*-
"""WF5 复杂流程：要素类 → DWG（反向导出）
    把 wf.gdb 的地块、用地融合导出成 AutoCAD DWG，并回读验证。

这是 CAD 入库的逆过程，规划出图交接常用。
前置：先跑 wf1_data_pipeline.py
"""
import os
import time

import arcpy

ROOT = r"A:\GisProTest\_wf_test"
GDB = os.path.join(ROOT, "wf.gdb")
OUT_DIR = os.path.join(ROOT, u"导出_dwg")
T0 = time.time()


def step(msg):
    print(u"[%5.1fs] %s" % (time.time() - T0, msg))


fc = os.path.join(GDB, u"地块")
if not arcpy.Exists(fc):
    raise RuntimeError(u"缺少 wf.gdb\\地块 —— 请先运行 wf1_data_pipeline.py")
if not os.path.isdir(OUT_DIR):
    os.makedirs(OUT_DIR)

dwg = os.path.join(OUT_DIR, u"地块.dwg")
if os.path.exists(dwg):
    os.remove(dwg)

# ---------- 1) 导出 DWG（AutoCAD 2018 格式）----------
arcpy.conversion.ExportCAD(fc, "DWG_R2018", dwg)
step(u"已导出 %s（%.1f KB）" % (os.path.basename(dwg), os.path.getsize(dwg) / 1024.0))

# ---------- 2) 回读验证：DWG 再当 CAD 读回来看看图层与要素 ----------
gdb2 = os.path.join(ROOT, "roundtrip.gdb")
if arcpy.Exists(gdb2):
    arcpy.management.Delete(gdb2)
arcpy.management.CreateFileGDB(ROOT, "roundtrip.gdb")
arcpy.env.referenceScale = 1000
arcpy.conversion.CADToGeodatabase(dwg, gdb2, "rt", 1000)
arcpy.env.workspace = gdb2
back = []
for ds in arcpy.ListDatasets("*", "Feature"):
    for f in arcpy.ListFeatureClasses("*", "", ds):
        n = int(arcpy.management.GetCount(os.path.join(gdb2, ds, f))[0])
        back.append("%s/%s(%d)" % (ds, f, n))
step(u"回读 DWG 成功：%s" % u"、".join(back))

# ---------- 3) 摘要 ----------
print(u"输出目录：%s" % OUT_DIR)
for f in sorted(os.listdir(OUT_DIR)):
    print(u"   %s  %.1f KB" % (f, os.path.getsize(os.path.join(OUT_DIR, f)) / 1024.0))
# 声明产物：DWG 不能上图，只提示导出位置
print(u"@@YGH-REVEAL " + dwg)   # DWG 不能上图 → 打开所在目录
step(u"WF5 全部完成")
