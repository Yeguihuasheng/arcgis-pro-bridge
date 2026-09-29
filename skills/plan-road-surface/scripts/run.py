# -*- coding: utf-8 -*-
"""
道路面与边线生成 —— ArcGIS Pro 版

由道路中心线按宽度字段生成道路面，再由道路面转成道路边线。宽度分组处理，避免缓冲区字段解析在不同数据源上的差异；用于村庄规划道路红线、路面范围快速成图。
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


def main(in_lines, width_field, out_poly, out_line):
    if not arcpy.Exists(in_lines):
        log(u"错误：输入图层不存在 %s" % in_lines)
        return 1
    names = [f.name for f in arcpy.ListFields(in_lines)]
    if width_field not in names:
        log(u"错误：图层里没有字段 %s，现有字段：%s"
            % (width_field, u",".join(names[:12])))
        return 1
    vals = {}
    with arcpy.da.SearchCursor(in_lines, [width_field]) as cur:
        for (w,) in cur:
            try:
                w = float(w or 0)
            except (TypeError, ValueError):
                w = 0.0
            if w <= 0:
                continue
            vals.setdefault(round(w, 3), 0)
            vals[round(w, 3)] += 1
    if not vals:
        log(u"错误：宽度字段没有可用的正值")
        return 1
    dq = arcpy.AddFieldDelimiters(in_lines, width_field)
    bufs = []
    i = 0
    for w in sorted(vals):
        i += 1
        lyr = u"rd_lyr_%d" % i
        where = u"%s = %s" % (dq, w)
        arcpy.MakeFeatureLayer_management(in_lines, lyr, where)
        buf = u"in_memory\rd_buf_%d" % i
        arcpy.Buffer_analysis(lyr, buf, u"%s Meters" % (w / 2.0),
                              u"FULL", u"ROUND", u"NONE")
        bufs.append(buf)
        log(u"  宽度 %s 米：%d 条" % (w, vals[w]))
    arcpy.Merge_management(bufs, out_poly)
    n_in = int(arcpy.GetCount_management(in_lines).getOutput(0))
    n_out = int(arcpy.GetCount_management(out_poly).getOutput(0))
    log(u"道路面：%s（输入 %d 条 -> 输出 %d 个面）" % (out_poly, n_in, n_out))
    if (out_line or u"").strip():
        arcpy.FeatureToLine_management([out_poly], out_line.strip())
        n_ln = int(arcpy.GetCount_management(out_line.strip()).getOutput(0))
        log(u"道路边线：%s（%d 条）" % (out_line.strip(), n_ln))
    for b in bufs:
        try:
            arcpy.Delete_management(b)
        except Exception:
            pass
    log(u"提醒：宽度为 0 或空的线段已跳过，请核对条数是否匹配")
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
    args = list(argv) + [""] * (4 - len(argv) if len(argv) < 4 else 0)
    return main(*args[:4])


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]) or 0)
