# -*- coding: utf-8 -*-
"""查找使用中的属性域—— ArcGIS Pro 版

扫描地理数据库内的所有要素类与表（含子类型），找出哪些字段引用了属性域，输出
「数据集, 子类型, 字段, 属性域」清单 CSV，用于清理冗余属性域、盘点属性域引用关系。
"""
from __future__ import print_function, unicode_literals

import csv
import io
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


def _find_in_use(item):
    result = []
    try:
        subtypes = arcpy.da.ListSubtypes(item)
    except Exception:
        return result
    for stcode, stdict in subtypes.items():
        name = stdict.get(u"Name") if stcode != 0 else u"None"
        fieldvals = stdict.get(u"FieldValues", {})
        for field, vals in fieldvals.items():
            # vals = [default, domain]
            if isinstance(vals, (list, tuple)) and len(vals) > 1 and vals[1] is not None:
                dom = vals[1]
                dom_name = getattr(dom, "name", None) or unicode(dom)
                result.append((item, unicode(name), field, dom_name))
    return result


def main(gdb, out_csv):
    if not gdb:
        log(__doc__)
        return 2
    if not arcpy.Exists(gdb):
        log(u"工作空间不存在：%s" % gdb)
        return 2

    arcpy.env.workspace = gdb
    rows = []
    items = list(arcpy.ListFeatureClasses() or []) + list(arcpy.ListTables() or [])
    if not items:
        log(u"工作空间内没有要素类或表。")
        return 0

    log(u"扫描 %d 个数据集……" % len(items))
    for item in items:
        for r in _find_in_use(item):
            rows.append(r)
            log(u"  %s | %s | %s | %s" % r)

    if out_csv:
        try:
            with io.open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f)
                w.writerow([u"数据集", u"子类型", u"字段", u"属性域"])
                for r in rows:
                    w.writerow(list(r))
            log(u"已写入 CSV：%s" % out_csv)
        except Exception as e:
            log(u"写 CSV 失败：%s" % err_text(e))

    log(u"完成：共找到 %d 处属性域引用。" % len(rows))
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
    args = list(argv) + [u""] * 2
    return main(args[0], args[1])


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]) or 0)
