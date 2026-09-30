# -*- coding: utf-8 -*-
"""坐标纠偏（WGS84 / GCJ-02 / BD09 互转）—— ArcGIS Pro 版

把要素类（点/线/面）的几何坐标在 WGS84、GCJ-02（国测局/火星坐标）、BD09（百度）
三种坐标系统之间互相转换，输出新要素类。用于把高德/百度等平台采集的坐标纠偏到
WGS84 或 CGCS2000 口径（本工具把 CGCS2000 按 WGS84 近似处理），或反向把标准坐标
偏置到平台坐标系以便套图。只改变平面坐标 X/Y，高程 Z 与 M 值原样保留；坐标系
定义（空间参考）不改变——这是「偏移纠偏」而非「投影变换」。
"""
from __future__ import print_function, unicode_literals

import os
import sys

import arcpy

arcpy.env.overwriteOutput = True

if sys.version_info[0] >= 3:
    unicode = str
    basestring = str


# ------------------------------------------------------------------ 纠偏数学
PI = 3.14159265358979323846264338327950288
A = 6378245.0
EE = 0.00669342162296594323


def out_of_china(lng, lat):
    return lng < 72.004 or lng > 137.8347 or lat < 0.8293 or lat > 55.8271


def _transformlat(lng, lat):
    import math
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat \
        + 0.2 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * PI) + 20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * PI) + 40.0 * math.sin(lat / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * PI) + 320.0 * math.sin(lat * PI / 30.0)) * 2.0 / 3.0
    return ret


def _transformlng(lng, lat):
    import math
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat \
        + 0.1 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * PI) + 20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * PI) + 40.0 * math.sin(lng / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * PI) + 300.0 * math.sin(lng / 30.0 * PI)) * 2.0 / 3.0
    return ret


def gcj02_to_wgs84(lng, lat):
    if out_of_china(lng, lat):
        return lng, lat
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    import math
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
    mglat = lat + dlat
    mglng = lng + dlng
    return lng * 2 - mglng, lat * 2 - mglat


def wgs84_to_gcj02(lng, lat):
    if out_of_china(lng, lat):
        return lng, lat
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    import math
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
    mglat = lat + dlat
    mglng = lng + dlng
    return mglng, mglat


def gcj02_to_bd09(lng, lat):
    import math
    x = lng
    y = lat
    z = math.sqrt(x * x + y * y) + 0.00002 * math.sin(y * PI * 3000.0 / 180.0)
    theta = math.atan2(y, x) + 0.000003 * math.cos(x * PI * 3000.0 / 180.0)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return bd_lng, bd_lat


def bd09_to_gcj02(bd_lng, bd_lat):
    import math
    x = bd_lng - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * PI * 3000.0 / 180.0)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * PI * 3000.0 / 180.0)
    gcj_lng = z * math.cos(theta)
    gcj_lat = z * math.sin(theta)
    return gcj_lng, gcj_lat


def wgs84_to_bd09(lng, lat):
    gcj_lng, gcj_lat = wgs84_to_gcj02(lng, lat)
    return gcj02_to_bd09(gcj_lng, gcj_lat)


def bd09_to_wgs84(bd_lng, bd_lat):
    gcj_lng, gcj_lat = bd09_to_gcj02(bd_lng, bd_lat)
    return gcj02_to_wgs84(gcj_lng, gcj_lat)


def _normalize(system):
    text = unicode(system).strip().upper()
    text = text.replace(u'（', u'(').replace(u'）', u')')
    text = text.replace(u'-', u'').replace(u'_', u'').replace(u' ', u'')
    if u'WGS84' in text or text == u'WGS':
        return u'WGS84'
    if u'CGCS2000' in text or u'CGCS' in text:
        return u'WGS84'
    if u'GCJ02' in text or u'GCJ' in text or u'国测局' in text:
        return u'GCJ02'
    if u'BD09' in text or u'BAIDU' in text or u'百度' in text:
        return u'BD09'
    return text


def convert_coord(lng, lat, from_system, to_system):
    from_key = _normalize(from_system)
    to_key = _normalize(to_system)
    if from_key == to_key:
        return lng, lat
    if from_key == u'WGS84' and to_key == u'GCJ02':
        return wgs84_to_gcj02(lng, lat)
    if from_key == u'WGS84' and to_key == u'BD09':
        return wgs84_to_bd09(lng, lat)
    if from_key == u'GCJ02' and to_key == u'WGS84':
        return gcj02_to_wgs84(lng, lat)
    if from_key == u'GCJ02' and to_key == u'BD09':
        return gcj02_to_bd09(lng, lat)
    if from_key == u'BD09' and to_key == u'GCJ02':
        return bd09_to_gcj02(lng, lat)
    if from_key == u'BD09' and to_key == u'WGS84':
        return bd09_to_wgs84(lng, lat)
    raise ValueError(u'不支持的坐标系转换：%s -> %s' % (from_system, to_system))


# ------------------------------------------------------------------ 通用
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


def _mkpt(p, from_sys, to_sys, has_z, has_m):
    x, y = convert_coord(p.X, p.Y, from_sys, to_sys)
    n = arcpy.Point()
    n.X = x
    n.Y = y
    if has_z:
        n.Z = p.Z
    if has_m:
        n.M = p.M
    return n


def transform_geometry(g, from_sys, to_sys):
    has_z = bool(getattr(g, "hasZ", False))
    has_m = bool(getattr(g, "hasM", False))
    gt = g.type
    if gt == u"point":
        return _mkpt(g.getPart(0), from_sys, to_sys, has_z, has_m)
    parts = []
    for i in range(g.partCount):
        arr = arcpy.Array()
        for p in g.getPart(i):
            if p is None:
                arr.add(None)
            else:
                arr.add(_mkpt(p, from_sys, to_sys, has_z, has_m))
        parts.append(arr)
    if gt == u"multipoint":
        return arcpy.Multipoint(parts[0], g.spatialReference)
    if gt == u"polyline":
        return arcpy.Polyline(parts, g.spatialReference)
    if gt == u"polygon":
        return arcpy.Polygon(parts, g.spatialReference)
    return g


def main(in_fc, out_fc, from_sys, to_sys):
    if not in_fc or not out_fc or not from_sys or not to_sys:
        log(__doc__)
        return 2
    try:
        _normalize(from_sys)
        _normalize(to_sys)
    except Exception as e:
        log(u"坐标系参数无法识别：%s" % err_text(e))
        return 2
    if not arcpy.Exists(in_fc):
        log(u"输入要素不存在：%s" % in_fc)
        return 2

    desc = arcpy.Describe(in_fc)
    log(u"输入：%s（%s，%d 个要素）" % (in_fc, desc.shapeType, _count(in_fc)))
    log(u"纠偏：%s -> %s" % (from_sys, to_sys))

    arcpy.CopyFeatures_management(in_fc, out_fc)
    changed = 0
    with arcpy.da.UpdateCursor(out_fc, [u"SHAPE@"]) as cur:
        for row in cur:
            g = row[0]
            if g is None:
                continue
            try:
                ng = transform_geometry(g, from_sys, to_sys)
            except Exception as e:
                log(u"  跳过一条（%s）" % err_text(e))
                continue
            cur.updateRow([ng])
            changed += 1
    log(u"完成：共转换 %d 个要素 -> %s" % (changed, out_fc))
    return 0


def _count(fc):
    try:
        return int(arcpy.GetCount_management(fc).getOutput(0))
    except Exception:
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
    if len(argv) < 1:
        log(__doc__)
        return 2
    args = list(argv) + [u""] * 4
    return main(args[0], args[1], args[2], args[3])


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]) or 0)
