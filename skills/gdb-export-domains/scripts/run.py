# -*- coding: utf-8 -*-
"""导出属性域值清单—— ArcGIS Pro 版

把地理数据库内所有「编码值属性域」（coded value domain）导出为同名表（写到该
GDB 内），可选再转成 Excel。用于属性域字典存档、跨库迁移、对外提供码表。
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


def main(gdb, do_xls):
    if not gdb:
        log(__doc__)
        return 2
    if not arcpy.Exists(gdb):
        log(u"工作空间不存在：%s" % gdb)
        return 2

    do_xls = unicode(do_xls).strip().lower() in (u"true", u"yes", u"1", u"y", u"是")

    domains = list(arcpy.da.ListDomains(gdb))
    if not domains:
        log(u"工作空间内没有属性域。")
        return 0

    ok_n = 0
    fail_n = 0
    for dom in domains:
        try:
            table = os.path.join(gdb, dom.name)
            arcpy.DomainToTable_management(gdb, dom.name, table,
                                           "field", "descript", "#")
            log(u"  已导出属性域表：%s" % dom.name)
            if do_xls:
                xlsfile = os.path.join(os.path.dirname(gdb),
                                       "%s_%s.xls" % (os.path.basename(gdb), dom.name))
                arcpy.TableToExcel_conversion(table, xlsfile)
                log(u"    另存 Excel：%s" % xlsfile)
            ok_n += 1
        except Exception as e:
            fail_n += 1
            log(u"  失败：%s（%s）" % (dom.name, err_text(e)))
    log(u"完成：导出 %d 个，失败 %d 个" % (ok_n, fail_n))
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
