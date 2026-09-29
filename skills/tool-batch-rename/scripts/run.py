# -*- coding: utf-8 -*-
"""
批量重命名数据集 —— ArcGIS Pro 版

对工作空间内的一批要素类/表批量改名，支持三种方式：加前缀、加后缀、查找替换（把名字里的某段文字换成另一段）。改名前列清单、改名后逐条汇报，遇到目标名已存在会跳过并报出来，不会覆盖已有数据。
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

def _norm(s):
    return (u"" if s is None else unicode(s)).strip()


def main(in_ws, mode, text1, text2):
    in_ws = _norm(in_ws)
    mode = _norm(mode)
    text1 = _norm(text1)
    text2 = _norm(text2)
    if not arcpy.Exists(in_ws):
        log(u"错误：工作空间不存在 %s" % in_ws)
        return 1
    if mode not in (u"加前缀", u"加后缀", u"查找替换"):
        log(u"错误：改名方式只能填「加前缀」「加后缀」「查找替换」，当前是「%s」" % mode)
        return 2
    if mode == u"查找替换" and not text1:
        log(u"错误：查找替换模式下必须填「要查找的文字」。")
        return 2

    old_ws = arcpy.env.workspace
    arcpy.env.workspace = in_ws
    try:
        fcs = list(arcpy.ListFeatureClasses() or [])
        tbs = list(arcpy.ListTables() or [])
        dss = list(arcpy.ListDatasets("", "Feature") or [])
        for ds in dss:
            for fc in (arcpy.ListFeatureClasses("", "", ds) or []):
                fcs.append(u"%s\\%s" % (ds, fc))
    finally:
        arcpy.env.workspace = old_ws

    items = [x for x in fcs + tbs if x]
    if not items:
        log(u"提示：工作空间内没有找到要素类或表。")
        return 0

    log(u"待改名对象：%d 个" % len(items))
    ok_n = skip_n = 0
    skipped = []
    for name in items:
        base = name.split(u"\\")[-1]
        parent = name[:len(name) - len(base)].rstrip(u"\\")
        if mode == u"加前缀":
            new_base = text1 + base
        elif mode == u"加后缀":
            new_base = base + text1
        else:
            new_base = base.replace(text1, text2) if text1 in base else base
        if new_base == base:
            skip_n += 1
            continue
        new_path = os.path.join(in_ws, parent, new_base) if parent \
            else os.path.join(in_ws, new_base)
        if arcpy.Exists(new_path):
            skip_n += 1
            skipped.append(u"%s（目标已存在）" % base)
            log(u"  跳过：%s -> %s（目标已存在）" % (base, new_base))
            continue
        try:
            arcpy.Rename_management(os.path.join(in_ws, name), new_path)
        except Exception as e:
            skip_n += 1
            skipped.append(u"%s（%s）" % (base, err_text(e)))
            log(u"  失败：%s（%s）" % (base, err_text(e)))
            continue
        ok_n += 1
        log(u"  %s -> %s" % (base, new_base))

    log(u"完成：改名 %d 个，跳过 %d 个" % (ok_n, skip_n))
    if skipped:
        log(u"跳过清单：%s" % u"；".join(skipped))
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
