# -*- coding: utf-8 -*-
"""1bit TIFF 批量转 8bit PNG—— ArcGIS Pro 版

把文件夹内所有 1bit 二值 TIFF 栅格批量转换为 8bit PNG（OneBitTo8Bit），输出到
指定文件夹。用于黑白扫描图、二值掩膜、单色影像的规范化转换。
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


def main(in_folder, out_folder):
    if not in_folder or not out_folder:
        log(__doc__)
        return 2
    if not os.path.isdir(in_folder):
        log(u"输入文件夹不存在：%s" % in_folder)
        return 2
    if not os.path.isdir(out_folder):
        try:
            os.makedirs(out_folder)
        except Exception as e:
            log(u"无法创建输出文件夹：%s" % err_text(e))
            return 2

    arcpy.env.workspace = in_folder
    rasters = arcpy.ListRasters(None, "TIF")
    if not rasters:
        rasters = arcpy.ListRasters(None, "TIFF")
    if not rasters:
        log(u"输入文件夹内没有 TIF 栅格。")
        return 0

    log(u"发现 %d 个 TIF 栅格，开始转换。" % len(rasters))
    ok_n = 0
    fail_n = 0
    for tiff in rasters:
        in_img = os.path.join(in_folder, tiff)
        base, _ext = os.path.splitext(tiff)
        out_img = os.path.join(out_folder, base + ".png")
        try:
            arcpy.CopyRaster_management(in_img, out_img, "", "", "",
                                        "OneBitTo8Bit", "NONE", "", "NONE", "NONE")
            log(u"  %s -> %s" % (tiff, os.path.basename(out_img)))
            ok_n += 1
        except Exception as e:
            fail_n += 1
            log(u"  失败：%s（%s）" % (tiff, err_text(e)))
    log(u"完成：成功 %d 个，失败 %d 个" % (ok_n, fail_n))
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
