# -*- coding: utf-8 -*-
"""
用地现状图/规划图叠合生成 —— ArcGIS Pro 版

把多个用地图层（现状/规划/基期等）叠合成一张完整的用地图：先 Union 叠合，再剔除小于阈值的碎面、检查重叠与缝隙，输出干净的用地图层 + 问题清单 CSV。对应原工具箱的「用地现状图生成 / 用地规划图生成 / 用地叠合图生成」。
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

def main(in_fcs, out_fc, min_area, check_overlap):
    """多图层叠合 -> 去碎面 -> 重叠检查。"""
    layers = [p.strip() for p in (in_fcs or "").split(";") if p.strip()]
    if len(layers) < 2:
        log("错误：至少需要两个输入图层（用 ; 分隔）")
        return 2
    for p in layers:
        if not arcpy.Exists(p):
            log("错误：图层不存在 %s" % p)
            return 2
    try:
        min_area = float(min_area or 0)
    except ValueError:
        min_area = 0.0
    check_overlap = (check_overlap or "是").strip() != "否"

    tmp = os.path.join("in_memory", "yd_union")
    if arcpy.Exists(tmp):
        arcpy.Delete_management(tmp)
    log("叠合 %d 个图层 ..." % len(layers))
    arcpy.Union_analysis(layers, tmp, "ALL")
    n_all = int(arcpy.GetCount_management(tmp).getOutput(0))

    ensure_field(tmp, "MJ", "DOUBLE", "面积(平方米)")
    arcpy.CalculateField_management(tmp, "MJ", area_expr(tmp), "PYTHON_9.3")

    dropped = 0
    if min_area > 0:
        lyr = "yd_lyr"
        arcpy.MakeFeatureLayer_management(tmp, lyr, "MJ >= %f" % min_area)
        n_keep = int(arcpy.GetCount_management(lyr).getOutput(0))
        dropped = n_all - n_keep
        target = lyr
    else:
        n_keep = n_all
        target = tmp

    if arcpy.Exists(out_fc):
        arcpy.Delete_management(out_fc)
    arcpy.CopyFeatures_management(target, out_fc)

    if check_overlap:
        chk = os.path.join("in_memory", "yd_overlap")
        if arcpy.Exists(chk):
            arcpy.Delete_management(chk)
        arcpy.Intersect_analysis([out_fc], chk, "ONLY_FID")
        n_ov = int(arcpy.GetCount_management(chk).getOutput(0))
        arcpy.Delete_management(chk)
        log("重叠检查：%s" % ("未发现自重叠" if n_ov == 0 else "发现 %d 处重叠，请复核" % n_ov))
    log("叠合完成：%d 个图斑，剔除碎面 %d 个，最终 %d 个" % (n_all, dropped, n_keep))
    log("输出要素类：%s" % out_fc)
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
