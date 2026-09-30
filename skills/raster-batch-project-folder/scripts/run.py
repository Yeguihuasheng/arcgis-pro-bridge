# -*- coding: utf-8 -*-
"""栅格文件夹批量投影—— ArcGIS Pro 版

把文件夹内所有栅格批量投影到指定坐标系，输出到新文件夹。用于一批影像/栅格统一
坐标系（如统一投到 Web Mercator 或 CGCS2000 高斯投影），替换逐张手动投影。
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


def main(in_folder, out_folder, out_sr, resampling, geo_transform):
    if not in_folder or not out_folder or not out_sr:
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

    resampling = resampling or u"NEAREST"
    geo_transform = geo_transform or u""

    arcpy.env.workspace = in_folder
    rasters = arcpy.ListRasters()
    if not rasters:
        log(u"输入文件夹内没有可识别的栅格。")
        return 0

    log(u"发现 %d 个栅格，投影到目标坐标系。" % len(rasters))
    ok_n = 0
    fail_n = 0
    for r in rasters:
        in_r = os.path.join(in_folder, r)
        out_r = os.path.join(out_folder, r)
        try:
            arcpy.ProjectRaster_management(in_r, out_r, out_sr,
                                           resampling, "", geo_transform)
            log(u"  %s -> %s" % (r, out_r))
            ok_n += 1
        except Exception as e:
            fail_n += 1
            log(u"  失败：%s（%s）" % (r, err_text(e)))
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
    if len(argv) < 3:
        log(__doc__)
        return 2
    args = list(argv) + [u""] * 5
    return main(args[0], args[1], args[2], args[3], args[4])


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]) or 0)
