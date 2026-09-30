# -*- coding: utf-8 -*-
"""Shapefile 批量打包 ZIP—— ArcGIS Pro 版

把文件夹内的每个 shapefile（连同 .shx/.dbf/.prj/.cpg/.sbn/.sbx/.xml 等附属文件）
分别打包成一个 ZIP，输出到指定文件夹；也支持直接传入单个 .shp 文件只打这一个。
用于成果移交、上传、归档时按规范打包。
"""
from __future__ import print_function, unicode_literals

import os
import sys
import zipfile

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


def _sidecar_files(shp_path):
    """返回与给定 .shp 同名前缀的所有附属文件路径。"""
    base = os.path.splitext(shp_path)[0]
    d = os.path.dirname(shp_path)
    out = []
    if os.path.isdir(d):
        for f in os.listdir(d):
            fp = os.path.join(d, f)
            if os.path.isfile(fp) and os.path.splitext(fp)[0].lower() == base.lower():
                out.append(fp)
    return out


def _zip_one(shp_path, out_folder):
    base = os.path.basename(shp_path)
    stem = os.path.splitext(base)[0]
    zip_path = os.path.join(out_folder, stem + ".zip")
    files = _sidecar_files(shp_path)
    if not files:
        log(u"  跳过：%s（未找到附属文件）" % base)
        return 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, os.path.basename(f))
    log(u"  %s -> %s（%d 个文件）" % (base, os.path.basename(zip_path), len(files)))
    return 1


def main(in_path, out_folder):
    if not in_path or not out_folder:
        log(__doc__)
        return 2
    if not os.path.isdir(out_folder):
        try:
            os.makedirs(out_folder)
        except Exception as e:
            log(u"无法创建输出文件夹：%s" % err_text(e))
            return 2

    # 单文件模式
    if os.path.isfile(in_path) and in_path.lower().endswith(u".shp"):
        ok = _zip_one(in_path, out_folder)
        log(u"完成：打包 %d 个 shapefile" % ok)
        return 0

    # 文件夹模式
    if not os.path.isdir(in_path):
        log(u"输入路径不存在：%s" % in_path)
        return 2

    shps = sorted(f for f in os.listdir(in_path) if f.lower().endswith(u".shp"))
    if not shps:
        log(u"输入文件夹内没有 .shp 文件。")
        return 0

    log(u"发现 %d 个 shapefile，开始打包。" % len(shps))
    ok_n = 0
    for f in shps:
        try:
            ok_n += _zip_one(os.path.join(in_path, f), out_folder)
        except Exception as e:
            log(u"  失败：%s（%s）" % (f, err_text(e)))
    log(u"完成：打包 %d 个 shapefile" % ok_n)
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
