# -*- coding: utf-8 -*-
"""WF1 复杂流程：从零建库 → 建要素类与字段 → 造 12 个地块要素 → 计算面积/建筑面积
                   → 按用地性质汇总统计 → 导出 shapefile → 建空间索引

全程在 Pro 进程内（QueuedTask 上下文）执行，输出会实时显示在 YghsBridge 面板里。
"""
import os
import time

import arcpy

ROOT = r"A:\GisProTest\_wf_test"
GDB = os.path.join(ROOT, "wf.gdb")
SR = arcpy.SpatialReference("CGCS2000_3_Degree_GK_CM_111E")
T0 = time.time()


def step(msg):
    print(u"[%5.1fs] %s" % (time.time() - T0, msg))


# ---------- 1) 干净的库 ----------
if not os.path.isdir(ROOT):
    os.makedirs(ROOT)
if arcpy.Exists(GDB):
    arcpy.management.Delete(GDB)
arcpy.management.CreateFileGDB(ROOT, "wf.gdb")
step(u"已创建文件地理数据库 wf.gdb")

# ---------- 2) 要素类 + 字段 ----------
FC = os.path.join(GDB, u"地块")
arcpy.management.CreateFeatureclass(GDB, u"地块", "POLYGON", spatial_reference=SR)
fields = [
    (u"地块编号", "TEXT", 20),
    (u"用地性质", "TEXT", 20),
    (u"容积率", "DOUBLE", None),
    (u"占地面积", "DOUBLE", None),
    (u"建筑面积", "DOUBLE", None),
    (u"备注", "TEXT", 100),
]
for name, typ, ln in fields:
    if typ == "TEXT":
        arcpy.management.AddField(FC, name, typ, field_length=ln)
    else:
        arcpy.management.AddField(FC, name, typ)
step(u"要素类「地块」已建，字段 %d 个" % len(fields))

# ---------- 3) 造 12 个地块（4 行 3 列网格，尺寸各异）----------
USES = [u"居住用地", u"商业用地", u"公共服务设施用地"]
rows, cols, x0, y0 = 4, 3, 500000.0, 3200000.0
data = []
for r in range(rows):
    for c in range(cols):
        idx = r * cols + c + 1
        w = 60 + (idx % 4) * 15          # 60~105 m
        h = 45 + (idx % 3) * 20          # 45~85 m
        cx = x0 + c * 160.0
        cy = y0 + r * 130.0
        ring = arcpy.Array([
            arcpy.Point(cx, cy), arcpy.Point(cx + w, cy),
            arcpy.Point(cx + w, cy + h), arcpy.Point(cx, cy + h),
            arcpy.Point(cx, cy),
        ])
        use = USES[(idx - 1) % len(USES)]
        far = 1.0 + (idx % 5) * 0.5      # 容积率 1.0~3.0
        # 注意顺序必须与 InsertCursor 的字段表一致：SHAPE@, 地块编号, 用地性质, 容积率
        data.append((arcpy.Polygon(ring, SR), u"DK%02d" % idx, use, far))

with arcpy.da.InsertCursor(FC, ["SHAPE@", u"地块编号", u"用地性质", u"容积率"]) as cur:
    for row in data:
        cur.insertRow(row)
step(u"已生成 %d 个地块要素" % len(data))

# ---------- 4) 计算占地面积 / 建筑面积 ----------
arcpy.management.CalculateField(FC, u"占地面积", "!shape.area!", "PYTHON3")
arcpy.management.CalculateField(FC, u"建筑面积", "!占地面积! * !容积率!", "PYTHON3")
step(u"已计算占地面积与建筑面积（建筑面积 = 占地面积 × 容积率）")

# ---------- 5) 汇总统计 ----------
out_stat = os.path.join(GDB, u"用地统计")
arcpy.analysis.Statistics(FC, out_stat, [[u"占地面积", "SUM"], [u"建筑面积", "SUM"]], u"用地性质")
step(u"已按用地性质汇总（%s）" % os.path.basename(out_stat))

# ---------- 6) 导出：要素类 → shapefile；统计表 → CSV ----------
SHP_DIR = os.path.join(ROOT, u"导出")
if not os.path.isdir(SHP_DIR):
    os.makedirs(SHP_DIR)
arcpy.conversion.FeatureClassToShapefile([FC], SHP_DIR)
arcpy.conversion.TableToTable(out_stat, SHP_DIR, u"用地统计.csv")
for f in (u"地块.shp",):
    p = os.path.join(SHP_DIR, f)
    if arcpy.Exists(p):
        arcpy.management.AddSpatialIndex(p)
step(u"已导出 shapefile 与统计 CSV 到 %s" % SHP_DIR)

# ---------- 7) 摘要（会进面板）----------
tot_land = tot_floor = 0.0
with arcpy.da.SearchCursor(FC, [u"占地面积", u"建筑面积"]) as cur:
    for a, b in cur:
        tot_land += a
        tot_floor += b
print(u"地块数：%d 个" % len(data))
print(u"占地合计：%.2f 平方米；建筑合计：%.2f 平方米" % (tot_land, tot_floor))
# 统计表的字段名由工具生成（中文名可能带前缀），这里动态取，避免猜名字
stat_fields = [f.name for f in arcpy.ListFields(out_stat)]
print(u"统计表字段：%s" % u"、".join(stat_fields))
cnt_field = next((n for n in stat_fields if n.upper().startswith("COUNT")), None)
quote = lambda n: u"%s" % n
cols = [u"用地性质", u"SUM_占地面积", u"SUM_建筑面积"] + ([cnt_field] if cnt_field else [])
with arcpy.da.SearchCursor(out_stat, cols) as cur:
    for row in cur:
        use, a, b = row[0], row[1], row[2]
        n = row[3] if cnt_field else u"-"
        print(u"  %s：%s 个地块，占地 %.2f，建筑 %.2f" % (use, n, a, b))
# 声明产物：插件会把这些自动加入当前地图 / 打开导出目录并在面板提示位置
print(u"@@YGH-ADD " + os.path.join(GDB, u"地块"))
print(u"@@YGH-ADD " + os.path.join(GDB, u"用地统计"))
print(u"@@YGH-REVEAL " + os.path.join(SHP_DIR, u"用地统计.csv"))   # CSV 不能上图 → 打开所在目录
step(u"WF1 全部完成")
