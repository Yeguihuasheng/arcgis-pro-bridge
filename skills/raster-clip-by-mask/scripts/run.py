# -*- coding: utf-8 -*-
"""
影像按范围批量裁剪 —— ArcGIS Pro 版

用一个矢量范围（如村界、项目红线）批量裁剪一批影像/DEM，输出按原文件名命名。逐张汇报裁剪前后行列数，失败的单独列出。相比手工在 ArcToolbox 里一张张点，适合分幅影像或多年份影像的批量切边。
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


def main(in_arg, clip_fc, out_ws):
    ins = _split(in_arg)
    out_ws = (u"" if out_ws is None else unicode(out_ws)).strip()
    if not ins:
        log(u"错误：至少要给一个输入栅格。")
        return 2
    if not arcpy.Exists(clip_fc):
        log(u"错误：裁剪范围不存在 %s" % clip_fc)
        return 1
    if not arcpy.Exists(out_ws):
        log(u"错误：输出位置不存在 %s" % out_ws)
        return 1
    if arcpy.Describe(clip_fc).shapeType != u"Polygon":
        log(u"错误：裁剪范围必须是面要素类，当前是「%s」。"
            % arcpy.Describe(clip_fc).shapeType)
        return 1

    ok_n = 0
    failed = []
    for r in ins:
        if not arcpy.Exists(r):
            failed.append(u"%s（不存在）" % os.path.basename(r))
            log(u"  跳过：%s（不存在）" % r)
            continue
        name = os.path.splitext(os.path.basename(r))[0]
        out = os.path.join(out_ws, name)
        # 输出位置与输入同库时，同名输出会被当成「覆盖自身」而报 ERROR 000670
        try:
            if os.path.abspath(out) == os.path.abspath(r):
                out = out + u"_clip"
                name = name + u"_clip"
        except Exception:
            pass
        try:
            arcpy.Clip_management(r, u"#", out, clip_fc, u"-9999", u"ClippingGeometry",
                                  u"NO_MAINTAIN_EXTENT")
        except Exception as e:
            failed.append(u"%s（%s）" % (name, err_text(e)))
            log(u"  失败：%s（%s）" % (name, err_text(e)))
            continue
        ok_n += 1
        try:
            d = arcpy.Describe(out)
            log(u"  %s：%s" % (name, getattr(d, u"bandCount", 1)))
        except Exception:
            log(u"  %s：完成" % name)
    log(u"完成：成功 %d 个，失败 %d 个" % (ok_n, len(failed)))
    if failed:
        log(u"失败清单：%s" % u"；".join(failed))
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
    args = list(argv) + [""] * (3 - len(argv) if len(argv) < 3 else 0)
    return main(*args[:3])


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]) or 0)
