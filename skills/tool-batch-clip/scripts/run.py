# -*- coding: utf-8 -*-
"""
批量裁剪 —— ArcGIS Pro 版

用一个裁剪范围批量裁一批图层（如按行政村界、按项目红线裁地形、影像范围、现状图斑）。逐层汇报裁剪前后要素数，空结果会明确报出来，方便判断是不是坐标系或范围给错了。
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


def _expand(in_arg):
    txt = (in_arg or u"").strip()
    if not txt:
        return []
    parts = [p.strip() for p in txt.split(u";") if p.strip()]
    if len(parts) == 1 and os.path.isdir(parts[0]):
        arcpy.env.workspace = parts[0]
        out = []
        for fc in (arcpy.ListFeatureClasses() or []):
            out.append(os.path.join(parts[0], fc))
        for ds in (arcpy.ListDatasets(u"", u"Feature") or []):
            for fc in (arcpy.ListFeatureClasses(u"", u"", ds) or []):
                out.append(os.path.join(parts[0], ds, fc))
        return out
    return parts


def main(clip_fc, in_arg, out_ws, strict):
    if not arcpy.Exists(clip_fc):
        log(u"错误：裁剪范围不存在 %s" % clip_fc)
        return 1
    fcs = _expand(in_arg)
    if not fcs:
        log(u"错误：没有解析到任何待裁剪图层")
        return 1
    if not os.path.isdir(out_ws):
        os.makedirs(out_ws)
    is_strict = (strict or u"").strip().startswith(u"是")
    ok_n = 0
    empty = []
    for fc in fcs:
        if not arcpy.Exists(fc):
            log(u"跳过（不存在）：%s" % fc)
            continue
        before = int(arcpy.GetCount_management(fc).getOutput(0))
        out = os.path.join(out_ws, os.path.basename(fc))
        try:
            arcpy.Clip_analysis(fc, clip_fc, out)
        except Exception as e:
            log(u"失败：%s（%s）" % (os.path.basename(fc), err_text(e)))
            if is_strict:
                return 1
            continue
        after = int(arcpy.GetCount_management(out).getOutput(0))
        if after == 0:
            empty.append(os.path.basename(fc))
            log(u"  空结果：%s（裁前 %d）" % (os.path.basename(fc), before))
        else:
            ok_n += 1
            log(u"  %s：%d -> %d" % (os.path.basename(fc), before, after))
    log(u"完成：成功 %d 个，空结果 %d 个" % (ok_n, len(empty)))
    if empty:
        log(u"空结果清单：%s" % u", ".join(empty))
        log(u"提醒：范围与图层坐标系不一致、或范围确实不压盖时都会为空，请先核对")
        if is_strict:
            return 1
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
