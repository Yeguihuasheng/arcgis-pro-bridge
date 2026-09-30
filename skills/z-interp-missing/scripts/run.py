# -*- coding: utf-8 -*-
"""线要素缺失 Z 值插补—— ArcGIS Pro 版

对 3D 线（polylineZ）要素，把缺失高程的折点（Z 为 0 或 None）沿线路按已知高程
折点做线性插值补全，输出新要素类。用于河网/管线/断面线高程缺漏补全，为后续纵剖
面、三维建模做准备。逐条线独立处理，不做线间合并。
"""
from __future__ import print_function, unicode_literals

import os
import sys

import arcpy

arcpy.env.overwriteOutput = True

if sys.version_info[0] >= 3:
    unicode = str
    basestring = str


def err_text(e):
    try:
        return unicode(e)
    except Exception:
        pass
    try:
        return str(e).decode("utf-8", "replace")
    except Exception:
        try:
            return str(e).decode("mbcs", "replace")
        except Exception:
            return u"（错误信息含无法解码的字符，已省略）"


def log(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode("gbk", "replace"))


def _dist2(p1, p2):
    return ((p2.X - p1.X) ** 2 + (p2.Y - p1.Y) ** 2) ** 0.5


def _interp_part(points):
    """对一条线（单个 part 的点数组）做缺失 Z 线性插补，返回新点数组。"""
    n = len(points)
    if n == 0:
        return points

    def _valid(p):
        z = p.Z
        if z is None:
            return False
        try:
            return abs(float(z)) > 1e-9
        except Exception:
            return False

    # 累计链长
    cum = [0.0]
    for i in range(1, n):
        cum.append(cum[-1] + _dist2(points[i - 1], points[i]))

    zs = [p.Z for p in points]
    # 标记有效高程折点下标
    valid_idx = [i for i in range(n) if _valid(points[i])]

    if len(valid_idx) == 0:
        return None  # 全无有效 Z，无法插补，交由上层原样保留
    if len(valid_idx) == 1:
        # 只有一个已知高程，无法线性插补，原样保留
        return None

    # 补齐两端：首/尾缺失时沿用最近已知高程
    first, last = valid_idx[0], valid_idx[-1]
    if first > 0:
        for i in range(0, first):
            zs[i] = zs[first]
    if last < n - 1:
        for i in range(last + 1, n):
            zs[i] = zs[last]

    # 已知点之间线性插值
    for a in range(len(valid_idx) - 1):
        i0 = valid_idx[a]
        i1 = valid_idx[a + 1]
        if i1 - i0 <= 1:
            continue
        z0 = zs[i0]
        z1 = zs[i1]
        d0 = cum[i0]
        d1 = cum[i1]
        span = d1 - d0
        if span <= 0:
            for i in range(i0 + 1, i1):
                zs[i] = z0
            continue
        for i in range(i0 + 1, i1):
            zs[i] = z0 + (z1 - z0) * (cum[i] - d0) / span

    out = arcpy.Array()
    for i in range(n):
        p = points[i]
        np_ = arcpy.Point()
        np_.X = p.X
        np_.Y = p.Y
        np_.Z = zs[i]
        if p.M is not None:
            np_.M = p.M
        out.add(np_)
    return out


def _interp_geometry(g):
    if g is None or g.type != u"polyline":
        return None
    parts = []
    changed = False
    for i in range(g.partCount):
        pts = [p for p in g.getPart(i) if p is not None]
        res = _interp_part(pts)
        if res is None:
            parts.append(arcpy.Array(pts))
        else:
            parts.append(res)
            changed = True
    if not changed:
        return None
    return arcpy.Polyline(parts, g.spatialReference)


def main(in_fc, out_fc):
    if not in_fc or not out_fc:
        log(__doc__)
        return 2
    if not arcpy.Exists(in_fc):
        log(u"输入要素不存在：%s" % in_fc)
        return 2

    desc = arcpy.Describe(in_fc)
    log(u"输入：%s（%s）" % (in_fc, desc.shapeType))

    arcpy.CopyFeatures_management(in_fc, out_fc)
    changed = 0
    skipped = 0
    with arcpy.da.UpdateCursor(out_fc, [u"SHAPE@"]) as cur:
        for row in cur:
            g = row[0]
            ng = _interp_geometry(g)
            if ng is None:
                skipped += 1
                continue
            cur.updateRow([ng])
            changed += 1
    log(u"完成：插补 %d 条线，未改 %d 条 -> %s" % (changed, skipped, out_fc))
    return 0


def _to_unicode(s):
    if not isinstance(s, bytes):
        return s
    for enc in (u"mbcs", u"utf-8", u"gbk", u"latin-1"):
        try:
            return s.decode(enc)
        except Exception:
            continue
    return s.decode(u"utf-8", u"replace")


def _main(argv):
    if sys.version_info[0] < 3:
        argv = [_to_unicode(a) for a in argv]
    if len(argv) < 2:
        log(__doc__)
        return 2
    return main(argv[0], argv[1])


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]) or 0)
