# -*- coding: utf-8 -*-
"""
多部件打散与几何修复 —— ArcGIS Pro 版

把多部件要素打散成单部件（一个图斑一个面），可选顺带跑一次几何修复并删掉空几何。多部件在用地统计、图斑编号、拓扑检查里经常出问题，入库前一般都要先打散。打散后汇报前后要素数变化。
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

def main(in_fc, out_fc, do_repair):
    out_fc = (u"" if out_fc is None else unicode(out_fc)).strip()
    repair = (u"" if do_repair is None else unicode(do_repair)).strip() \
        in (u"是", u"Y", u"y", u"1", u"True")
    if not arcpy.Exists(in_fc):
        log(u"错误：输入要素类不存在 %s" % in_fc)
        return 1
    if not out_fc:
        log(u"错误：必须填输出要素类。")
        return 2
    desc = arcpy.Describe(in_fc)
    if desc.shapeType not in (u"Polygon", u"Polyline", u"Multipoint"):
        log(u"提示：输入是「%s」，多部件打散对面/线/多点才有意义。" % desc.shapeType)

    before = int(arcpy.GetCount_management(in_fc).getOutput(0))
    log(u"打散前：%d 个要素" % before)
    arcpy.MultipartToSinglepart_management(in_fc, out_fc)
    after = int(arcpy.GetCount_management(out_fc).getOutput(0))
    log(u"打散后：%d 个要素（+ %d）" % (after, after - before))

    if repair:
        try:
            res = arcpy.RepairGeometry_management(out_fc, u"DELETE_NULL")
            log(u"已修复几何：%s" % (res.getMessages(0).strip().splitlines() or [u"完成"])[-1][:120])
        except Exception as e:
            log(u"警告：修复几何未执行（%s）" % err_text(e))
        n2 = int(arcpy.GetCount_management(out_fc).getOutput(0))
        if n2 != after:
            log(u"修复并删除空几何后：%d 个要素（- %d）" % (n2, after - n2))

    multi = 0
    with arcpy.da.SearchCursor(out_fc, [u"SHAPE@"]) as cur:
        for (g,) in cur:
            if g is not None and getattr(g, u"isMultipart", False):
                multi += 1
    log(u"复核：剩余多部件 %d 个" % multi)
    if multi:
        log(u"提醒：仍有 %d 个多部件，可能是打散工具对某些几何无效，请人工核对。" % multi)
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
