# -*- coding: utf-8 -*-
"""
属性表导出 CSV / Excel —— ArcGIS Pro 版

把要素类或表的属性导出成 CSV 或 Excel，供统计、上报、对外交付。可只导出指定字段（留空为全部），CSV 走 UTF-8 带 BOM，Excel 直接打开的中文不会乱码。导出后汇报行数与列数。
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

def _split(s):
    if not s:
        return []
    return [x.strip() for x in unicode(s).replace(u"；", u";").split(u";")
            if x.strip()]


def main(in_tab, out_path, fields_arg):
    out_path = (u"" if out_path is None else unicode(out_path)).strip()
    if not arcpy.Exists(in_tab):
        log(u"错误：输入表不存在 %s" % in_tab)
        return 1
    if not out_path:
        log(u"错误：必须填输出文件路径。")
        return 2

    usable = []
    for f in arcpy.ListFields(in_tab):
        if f.type in (u"Geometry", u"Raster", u"Blob"):
            continue
        usable.append((f.name, f.type))
    want = _split(fields_arg)
    if want:
        low = dict((n.upper(), n) for n, _ in usable)
        picked = []
        for w in want:
            if w.upper() in low:
                picked.append(low[w.upper()])
            else:
                log(u"警告：字段「%s」不存在，已跳过。" % w)
        if not picked:
            log(u"错误：指定的字段都不存在。可用字段：%s"
                % u"，".join(n for n, _ in usable))
            return 1
    else:
        picked = [n for n, _ in usable]

    low = out_path.lower()
    if low.endswith(u".csv"):
        rows = []
        with arcpy.da.SearchCursor(in_tab, picked) as cur:
            for r in cur:
                rows.append([u"" if v is None else unicode(v) for v in r])
        write_csv(out_path, picked, rows)
        log(u"完成：导出 %d 行 × %d 列 -> %s" % (len(rows), len(picked), out_path))
        return 0

    if low.endswith(u".xls") or low.endswith(u".xlsx"):
        if not hasattr(arcpy, u"TableToExcel_conversion"):
            log(u"错误：当前 ArcGIS 版本没有 TableToExcel 工具，请改用 .csv 输出。")
            return 1
        try:
            arcpy.TableToExcel_conversion(in_tab, out_path,
                                          u"Name", u"Code",
                                          u";".join(picked))
        except Exception:
            # 部分版本不支持 Field 参数，退化为整表导出
            arcpy.TableToExcel_conversion(in_tab, out_path)
        log(u"完成：导出 -> %s" % out_path)
        log(u"  字段：%s" % u"，".join(picked))
        return 0

    log(u"错误：输出文件后缀必须是 .csv 或 .xls / .xlsx，当前是 %s" % out_path)
    return 2



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
    args = list(argv) + [""] * (3 - len(argv) if len(argv) < 3 else 0)
    return main(*args[:3])


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]) or 0)
