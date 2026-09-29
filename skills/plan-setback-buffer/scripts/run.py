# -*- coding: utf-8 -*-
"""
控制线与退距管控范围 —— ArcGIS Pro 版

按给定距离生成控制线管控范围（河道蓝线、道路退距、设施防护距离、生态红线缓冲等），可选把结果融合成一张面，并统计范围内被影响的图斑与面积，输出明细表供复核。
"""
from __future__ import print_function, unicode_literals

import csv
import io
import os
import sys

import arcpy

arcpy.env.overwriteOutput = True

if sys.version_info[0] >= 3:
    # py3 没有 unicode/basestring，业务代码统一按 py2 写法调用这两个名字
    unicode = str
    basestring = str


def err_text(e):
    """异常信息里常混着 arcpy 返回的本地编码字节，直接参与 u"" 格式化会在 py2 下抛
    UnicodeDecodeError，统一走这里转成安全的 unicode。"""
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


def is_geographic(dataset):
    try:
        return arcpy.Describe(dataset).spatialReference.type == "Geographic"
    except Exception:
        return False


def area_expr(dataset):
    """「计算字段」用的面积表达式（不是游标字段名，别混用）。"""
    if is_geographic(dataset):
        return "!shape.geodesicArea@squaremeters!"
    return "!shape.area@squaremeters!"


def area_field(dataset):
    """da 游标用的面积字段，配合 area_value() 换算成平方米。

    坑：!shape.area@squaremeters! 只给 CalculateField 用；游标里写它直接
    「Cannot find field」。游标用 SHAPE@AREA，但地理坐标系下它是平方度，
    非米制投影坐标系下也不是平方米，这两种情况退回 SHAPE@ 手算测地面积。
    """
    try:
        sr = arcpy.Describe(dataset).spatialReference
    except Exception:
        return "SHAPE@"
    if sr.type == "Geographic":
        return "SHAPE@"
    unit = (sr.linearUnitName or u"").lower()
    if unit.startswith(u"meter") or unit.startswith(u"米"):
        return "SHAPE@AREA"
    return "SHAPE@"


def area_value(v):
    """把游标取出的面积值统一成平方米（数值或几何对象都接受）。"""
    if v is None:
        return 0.0
    if hasattr(v, "getArea"):
        try:
            return v.getArea("GEODESIC", "SQUAREMETERS")
        except Exception:
            try:
                return v.getArea("PLANAR", "SQUAREMETERS")
            except Exception:
                return getattr(v, "area", 0.0) or 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def ensure_field(dataset, name, ftype, alias, length=None):
    names = [f.name for f in arcpy.ListFields(dataset)]
    if name in names:
        return name
    arcpy.AddField_management(dataset, name, ftype, field_alias=alias,
                              field_length=length)
    return name


def to_text(dataset):
    """in_memory 中间层落盘；输出到普通文件夹时补 .shp。"""
    return dataset


def write_csv(path, header, rows):
    if sys.version_info[0] < 3:
        with io.open(path, "wb") as fh:
            w = csv.writer(fh)
            w.writerow([c.encode("utf-8") for c in header])
            for r in rows:
                w.writerow([(u"%s" % c).encode("utf-8") for c in r])
    else:
        with io.open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            for r in rows:
                w.writerow([u"%s" % c for c in r])
    return path


def main(in_fc, distance, out_fc, dissolve, stat_fc, out_csv):
    if not arcpy.Exists(in_fc):
        log(u"错误：输入图层不存在 %s" % in_fc)
        return 1
    try:
        dist = float(distance)
    except (TypeError, ValueError):
        log(u"错误：退距不是数字 %s" % distance)
        return 1
    do_dis = (dissolve or u"").strip().startswith(u"是")
    arcpy.Buffer_analysis(in_fc, out_fc, u"%s Meters" % dist, u"FULL",
                          u"ROUND", u"ALL" if do_dis else u"NONE")
    n = int(arcpy.GetCount_management(out_fc).getOutput(0))
    area = area_field(out_fc)
    tot = 0.0
    with arcpy.da.SearchCursor(out_fc, [area]) as cur:
        for (a,) in cur:
            tot += area_value(a)
    log(u"管控范围：%s（%d 个面）" % (out_fc, n))
    log(u"总面积 %.2f 平方米 = %.4f 亩 = %.6f 公顷"
        % (tot, tot / 666.6666667, tot / 10000.0))
    if (stat_fc or u"").strip() and (out_csv or u"").strip():
        s = stat_fc.strip()
        if not arcpy.Exists(s):
            log(u"警告：被影响图层不存在，跳过统计 %s" % s)
            return 0
        inter = u"in_memory\sb_inter"
        arcpy.Intersect_analysis([s, out_fc], inter, u"ALL")
        rows = []
        ia = area_field(inter)
        with arcpy.da.SearchCursor(inter, [ia]) as cur:
            for (a,) in cur:
                rows.append([round(area_value(a), 2)])
        write_csv(out_csv.strip(), [u"相交面积_平方米"], rows)
        n_i = int(arcpy.GetCount_management(inter).getOutput(0))
        log(u"被影响图斑 %d 个，明细表：%s" % (n_i, out_csv.strip()))
        try:
            arcpy.Delete_management(inter)
        except Exception:
            pass
    return 0



def _to_unicode(s):
    """py2 下 sys.argv 是字节串，中文参数不解码就和 u"" 比较会抛
    UnicodeDecodeError，所以入口统一转成 unicode。"""
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
    args = list(argv) + [""] * (6 - len(argv) if len(argv) < 6 else 0)
    return main(*args[:6])


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]) or 0)
