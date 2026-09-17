# -*- coding: utf-8 -*-
"""WF2 复杂流程：DWG → CAD 转 GDB → 各图层统计 → 散字文本空间聚类成"路名"
                → 导出点要素类与线/面要素类 → 建空间索引

为什么这么做：真实规划底图里路名常常是**一个字一个 Text 实体**（"规" "划" "一" "路"），
要还原成词语必须做空间聚类 —— 这是纯 arcpy 的活，正好压一压进程内通道。
"""
import os
import time

import arcpy

DWG = r"A:\GisProTest\test.dwg"
ROOT = r"A:\GisProTest\_wf_test"
GDB = os.path.join(ROOT, "cad.gdb")
SR = arcpy.SpatialReference("CGCS2000_3_Degree_GK_CM_111E")
T0 = time.time()


def step(msg):
    print(u"[%5.1fs] %s" % (time.time() - T0, msg))


if not os.path.isdir(ROOT):
    os.makedirs(ROOT)
if arcpy.Exists(GDB):
    arcpy.management.Delete(GDB)
arcpy.management.CreateFileGDB(ROOT, "cad.gdb")

# ---------- 1) CAD → GDB ----------
arcpy.env.referenceScale = 1000
arcpy.conversion.CADToGeodatabase(DWG, GDB, "cad", 1000, SR)
arcpy.env.workspace = GDB
layers = arcpy.ListFeatureClasses("*", "", "cad")
DS = os.path.join(GDB, "cad")
step(u"CAD 已入库，图层 %d 个" % len(layers))
for lyr in layers:
    p = os.path.join(DS, lyr)
    d = arcpy.Describe(p)
    step(u"   %-12s %-9s 要素 %d" % (lyr, d.shapeType, int(arcpy.management.GetCount(p)[0])))

# ---------- 2) 读散字文本 ----------
pts = []
with arcpy.da.SearchCursor(os.path.join(DS, "TextPoint"), ["SHAPE@", "Text"]) as cur:
    for shp, txt in cur:
        if not txt:
            continue
        t = txt.replace(u"\r", u"").replace(u"\n", u"").strip()
        if t:
            c = shp.centroid
            pts.append((c.X, c.Y, t))
step(u"读到 %d 个文字实体" % len(pts))

# ---------- 3) 自适应阈值：看最近邻距离的**小距离分位**（同词字符间距小，孤立编号距离大）----------
def nearest_dist(p, others):
    best = None
    for q in others:
        d2 = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
        if d2 > 0 and (best is None or d2 < best):
            best = d2
    return best ** 0.5 if best else 0.0


sample = pts[::max(1, len(pts) // 300)]
dists = sorted(nearest_dist(p, pts) for p in sample)
pct = lambda q: dists[min(len(dists) - 1, int(len(dists) * q))]
step(u"最近邻距离分位：p10=%.1f  p25=%.1f  p50=%.1f  p90=%.1f"
     % (pct(0.10), pct(0.25), pct(0.50), pct(0.90)))
# 同词字符的间距落在最小那一档，取 p10 附近作阈值；孤立编号因距离大而不会被误并
THRESH = max(pct(0.10) * 1.5, 0.5)
MAX_WORD = 12
step(u"聚类阈值 %.2f（单词上限 %d 字）" % (THRESH, MAX_WORD))

# ---------- 4) 单链聚类（半径 THRESH，串到上限即停）----------
used = [False] * len(pts)
groups = []
for i in range(len(pts)):
    if used[i]:
        continue
    used[i] = True
    chain = [i]
    while len(chain) < MAX_WORD:
        last = pts[chain[-1]]
        best, bestd = None, THRESH
        for j in range(len(pts)):
            if used[j]:
                continue
            d = ((last[0] - pts[j][0]) ** 2 + (last[1] - pts[j][1]) ** 2) ** 0.5
            if d <= bestd:
                best, bestd = j, d
        if best is None:
            break
        used[best] = True
        chain.append(best)
    groups.append(chain)
_words = [u"".join(pts[k][2] for k in sorted(c, key=lambda i: (pts[i][0], pts[i][1])))
          for c in groups]
_multi = [w for w in _words if len(w) > 1]
step(u"聚合成 %d 个词（多字词 %d 个，最长 %d 字）"
     % (len(_words), len(_multi), max((len(w) for w in _words), default=0)))

# ---------- 5) 写词语点要素类 ----------
NAMES = os.path.join(GDB, u"文字聚合")
arcpy.management.CreateFeatureclass(GDB, u"文字聚合", "POINT", spatial_reference=SR)
for n, typ, ln in ((u"名称", "TEXT", 100), (u"字数", "SHORT", None)):
    if typ == "TEXT":
        arcpy.management.AddField(NAMES, n, typ, field_length=ln)
    else:
        arcpy.management.AddField(NAMES, n, typ)

with arcpy.da.InsertCursor(NAMES, ["SHAPE@", u"名称", u"字数"]) as cur:
    for chain in groups:
        # 按词内字符的实际书写顺序还原（先按 X 再按 Y，兼容横排）
        members = sorted(chain, key=lambda k: (pts[k][0], pts[k][1]))
        word = u"".join(pts[k][2] for k in members)[:100]
        cx = sum(pts[k][0] for k in members) / len(members)
        cy = sum(pts[k][1] for k in members) / len(members)
        cur.insertRow([arcpy.Point(cx, cy), word, len(members)])
step(u"已写入「文字聚合」点要素类")

# ---------- 6) 导出 ----------
OUT = os.path.join(ROOT, u"导出_cad")
if not os.path.isdir(OUT):
    os.makedirs(OUT)
targets = [os.path.join(DS, "Polyline"), os.path.join(DS, "Polygon"), NAMES]
for t in targets:
    base = os.path.basename(t)
    if arcpy.Exists(t):
        arcpy.conversion.FeatureClassToShapefile([t], OUT)
        shp = os.path.join(OUT, base + u".shp")
        if arcpy.Exists(shp):
            arcpy.management.AddSpatialIndex(shp)
step(u"已导出 shp 到 %s" % OUT)

# ---------- 7) 摘要（会进面板）----------
words = [u"".join(pts[k][2] for k in sorted(c, key=lambda i: (pts[i][0], pts[i][1])))
         for c in groups]
longest = sorted(words, key=len, reverse=True)[:8]
print(u"文字实体 %d 个，聚合为 %d 个词" % (len(pts), len(groups)))
print(u"最长的词：%s" % u"、".join(longest))
# 声明产物
print(u"@@YGH-ADD " + os.path.join(GDB, u"文字聚合"))
step(u"WF2 全部完成")
