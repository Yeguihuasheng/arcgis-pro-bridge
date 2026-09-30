# -*- coding: utf-8 -*-
"""选中要素另存为图层—— ArcGIS Pro 版

把图层中「当前选中的要素」复制成一个新的独立要素类/图层（只含选中要素），用于把
一次交互选择的结果固化为可复用的数据，替代右键「根据所选要素创建图层」的脚本化
版本。
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


def main(layer, out_fc):
    if not layer or not out_fc:
        log(__doc__)
        return 2
    if not arcpy.Exists(layer):
        log(u"输入图层不存在：%s" % layer)
        return 2

    desc = arcpy.Describe(layer)
    if not hasattr(desc, "FIDSet"):
        log(u"输入不是图层（无法读取选择集），请传入带选择的图层。")
        return 2
    sel = desc.FIDSet
    if not sel:
        log(u"图层当前没有选中任何要素，已中止。")
        return 2

    log(u"图层：%s，选中 %d 个要素（%s）" % (desc.name, _fid_count(sel), sel))

    arcpy.CopyFeatures_management(layer, out_fc)
    n = 0
    try:
        n = int(arcpy.GetCount_management(out_fc).getOutput(0))
    except Exception:
        pass
    log(u"完成：已将选中要素另存为 %s（%d 个要素）" % (out_fc, n))
    return 0


def _fid_count(fidset):
    """FIDSet 形如 '0;1;2' 或 '0-9' 或混合，尽量算出数量。"""
    n = 0
    for part in fidset.split(u";"):
        part = part.strip()
        if not part:
            continue
        if u"-" in part:
            a, b = part.split(u"-", 1)
            try:
                n += int(b) - int(a) + 1
            except Exception:
                n += 1
        else:
            n += 1
    return n


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
