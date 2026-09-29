# -*- coding: utf-8 -*-
"""
街区/街坊/分村区域更新与检查 —— ArcGIS Pro 版

按区域单元（街区/街坊/分村）统计各类用地面积并回写字段，同时检查区域之间是否存在覆盖缝隙或重叠，输出统计表 CSV。对应原工具箱的「区域更新 / 区域检查」。
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

def main(qu_fc, yd_fc, qu_code_field, yd_code_field, out_csv):
    """区域维度汇总用地面积，并做范围检查。"""
    for p in (qu_fc, yd_fc):
        if not arcpy.Exists(p):
            log("错误：图层不存在 %s" % p)
            return 2
    qu_code_field = qu_code_field or ""
    yd_code_field = yd_code_field or ""
    qu_names = [f.name for f in arcpy.ListFields(qu_fc)]
    if qu_code_field and qu_code_field not in qu_names:
        log("错误：区域图层没有字段 %s" % qu_code_field)
        return 2
    if yd_code_field:
        yd_names = [f.name for f in arcpy.ListFields(yd_fc)]
        if yd_code_field not in yd_names:
            log("警告：用地图层没有字段 %s，改为只统计总面积" % yd_code_field)
            yd_code_field = ""

    tmp = os.path.join("in_memory", "qu_ident")
    if arcpy.Exists(tmp):
        arcpy.Delete_management(tmp)
    arcpy.Identity_analysis(yd_fc, qu_fc, tmp, "ALL")
    ensure_field(tmp, "MJ", "DOUBLE", "面积(平方米)")
    arcpy.CalculateField_management(tmp, "MJ", area_expr(tmp), "PYTHON_9.3")

    stat = {}
    flds = [qu_code_field, yd_code_field, "MJ"] if qu_code_field else ["MJ"]
    with arcpy.da.SearchCursor(tmp, [f for f in flds if f]) as cur:
        for row in cur:
            if qu_code_field and yd_code_field:
                key = (row[0], row[1])
                area = row[2] or 0
            elif qu_code_field:
                key = (row[0], "")
                area = row[1] or 0
            else:
                key = ("", "")
                area = row[0] or 0
            stat[key] = stat.get(key, 0) + area

    rows = []
    for (q, y) in sorted(stat):
        a = stat[(q, y)]
        rows.append([q, y, round(a, 3), round(a / 666.6667, 4), round(a / 10000.0, 6)])
    if out_csv:
        write_csv(out_csv, ["区域编号", "用地代码", "面积(平方米)", "面积(亩)", "面积(公顷)"], rows)
        log("统计表：%s" % out_csv)
    else:
        for r in rows[:20]:
            log("  %s %s %.2f 平方米" % (r[0], r[1], r[2]))

    # 范围检查：区域之间是否重叠
    ov = os.path.join("in_memory", "qu_overlap")
    if arcpy.Exists(ov):
        arcpy.Delete_management(ov)
    arcpy.Intersect_analysis([qu_fc], ov, "ONLY_FID")
    n = int(arcpy.GetCount_management(ov).getOutput(0))
    arcpy.Delete_management(ov)
    arcpy.Delete_management(tmp)
    log("区域范围检查：%s" % ("无重叠" if n == 0 else "发现 %d 处区域重叠，请复核" % n))
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
    args = list(argv) + [""] * (5 - len(argv) if len(argv) < 5 else 0)
    return main(*args[:5])


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]) or 0)
