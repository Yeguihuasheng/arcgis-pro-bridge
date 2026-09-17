# -*- coding: utf-8 -*-
"""WF3 复杂流程：GP 工具链 + 规模压力
    生成 2000 个随机点 → 地块做 25m 缓冲区 → 空间连接统计每块地的点数
    → 按用地性质融合 → 汇总统计 → 导出 CSV

用到的 GP：CreateRandomPoints / Buffer / SpatialJoin / Dissolve / Statistics / TableToTable
前置：先跑 wf1_data_pipeline.py（提供 wf.gdb\地块）
"""
import os
import time

import arcpy

ROOT = r"A:\GisProTest\_wf_test"
GDB = os.path.join(ROOT, "wf.gdb")
FC = os.path.join(GDB, u"地块")
OUT = os.path.join(ROOT, u"导出")
T0 = time.time()


def step(msg):
    print(u"[%5.1fs] %s" % (time.time() - T0, msg))


if not arcpy.Exists(FC):
    raise RuntimeError(u"缺少 wf.gdb\\地块 —— 请先运行 wf1_data_pipeline.py")
if not os.path.isdir(OUT):
    os.makedirs(OUT)

# ---------- 1) 2000 个随机点（先把范围做成环境设置）----------
arcpy.env.workspace = GDB
desc = arcpy.Describe(FC)
arcpy.env.outputCoordinateSystem = desc.spatialReference
arcpy.env.extent = desc.extent
PTS = os.path.join(GDB, u"随机点")
if arcpy.Exists(PTS):
    arcpy.management.Delete(PTS)
arcpy.management.CreateRandomPoints(GDB, u"随机点", number_of_points_or_field=2000)
step(u"已生成随机点 %d 个" % int(arcpy.management.GetCount(PTS)[0]))

# ---------- 2) 地块缓冲 25 米 ----------
BUF = os.path.join(GDB, u"地块_缓冲25")
arcpy.analysis.Buffer(FC, BUF, "25 Meters", dissolve_option="NONE")
step(u"已生成缓冲区 %d 个" % int(arcpy.management.GetCount(BUF)[0]))

# ---------- 3) 空间连接：每个缓冲区内有多少个点 ----------
SJ = os.path.join(GDB, u"缓冲_点统计")
arcpy.analysis.SpatialJoin(BUF, PTS, SJ, "JOIN_ONE_TO_ONE", "KEEP_ALL",
                           match_option="INTERSECT")
step(u"空间连接完成（%d 行）" % int(arcpy.management.GetCount(SJ)[0]))

# ---------- 4) 按用地性质融合 ----------
DIS = os.path.join(GDB, u"用地融合")
arcpy.management.Dissolve(FC, DIS, u"用地性质")
step(u"按用地性质融合得到 %d 个要素" % int(arcpy.management.GetCount(DIS)[0]))

# ---------- 5) 汇总 + 导出 CSV ----------
STAT = os.path.join(GDB, u"缓冲点统计汇总")
cnt_field = u"Join_Count"
sj_fields = [f.name for f in arcpy.ListFields(SJ)]
if cnt_field not in sj_fields:
    cnt_field = next((n for n in sj_fields if n.lower().startswith("join_count")), cnt_field)
arcpy.analysis.Statistics(SJ, STAT, [[cnt_field, "SUM"], [cnt_field, "MEAN"]], u"用地性质")
arcpy.conversion.TableToTable(STAT, OUT, u"缓冲点统计.csv")
arcpy.conversion.FeatureClassToShapefile([DIS, BUF], OUT)
step(u"已导出 CSV 与 shapefile 到 %s" % OUT)

# ---------- 6) 摘要 ----------
tot_pts = int(arcpy.management.GetCount(PTS)[0])
print(u"随机点：%d 个；缓冲面：%d 个" % (tot_pts, int(arcpy.management.GetCount(BUF)[0])))
with arcpy.da.SearchCursor(SJ, [u"地块编号", u"用地性质", cnt_field]) as cur:
    rows = sorted(cur, key=lambda r: -r[2])
for code, use, n in rows[:5]:
    print(u"  %s（%s）落在缓冲区内 %d 个点" % (code, use, n))
with arcpy.da.SearchCursor(STAT, [u"用地性质", u"SUM_" + cnt_field, u"MEAN_" + cnt_field]) as cur:
    for use, s, m in cur:
        print(u"  %s：合计 %d 个点，平均每块地 %.1f 个" % (use, s, m))
# 声明产物
print(u"@@YGH-ADD " + os.path.join(GDB, u"地块_缓冲25"))
print(u"@@YGH-ADD " + DIS)
print(u"@@YGH-REVEAL " + os.path.join(OUT, u"缓冲点统计.csv"))   # CSV 不能上图 → 打开所在目录
step(u"WF3 全部完成")
