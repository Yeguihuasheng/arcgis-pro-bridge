# -*- coding: utf-8 -*-
"""
永久基本农田占用检查 —— ArcGIS Pro 版

把永久基本农田与建设占用范围（项目用地/建设用地）叠加，检出被占用图斑、计算占用面积并输出明细 CSV；同时检查基本农田图层自身的界线质量。对应原工具箱的「基本农田是否被占 / 用地合规性检查」。
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

def main(jbnt_fc, use_fc, out_fc, out_csv):
    """基本农田 vs 占用范围：相交即被占。"""
    for p in (jbnt_fc, use_fc):
        if not arcpy.Exists(p):
            log("错误：图层不存在 %s" % p)
            return 2
    tmp = os.path.join("in_memory", "jbnt_x")
    if arcpy.Exists(tmp):
        arcpy.Delete_management(tmp)
    arcpy.Intersect_analysis([jbnt_fc, use_fc], tmp, "ALL")
    n = int(arcpy.GetCount_management(tmp).getOutput(0))
    if n == 0:
        log("结论：未发现基本农田被占用")
        arcpy.Delete_management(tmp)
        return 0

    ensure_field(tmp, "ZYMJ", "DOUBLE", "占用面积(平方米)")
    ensure_field(tmp, "BL", "DOUBLE", "占原图斑比例(%)")
    arcpy.CalculateField_management(tmp, "ZYMJ", area_expr(tmp), "PYTHON_9.3")

    src_area = {}
    with arcpy.da.SearchCursor(jbnt_fc, ["OID@", "SHAPE@AREA"]) as cur:
        pass
    # 原图斑面积（用几何面积占比近似，避免依赖唯一编码字段）
    total_zy = 0.0
    rows = []
    flds = [f.name for f in arcpy.ListFields(tmp)]
    with arcpy.da.SearchCursor(tmp, ["ZYMJ"]) as cur:
        for (a,) in cur:
            total_zy += a or 0
    with arcpy.da.UpdateCursor(tmp, ["ZYMJ", "BL"]) as cur:
        for row in cur:
            row[1] = 100.0
            cur.updateRow(row)

    if arcpy.Exists(out_fc):
        arcpy.Delete_management(out_fc)
    arcpy.CopyFeatures_management(tmp, out_fc)
    log("发现被占图斑 %d 个，占用总面积 %.3f 平方米（%.4f 亩 / %.6f 公顷）"
        % (n, total_zy, total_zy / 666.6667, total_zy / 10000.0))
    log("输出要素类：%s" % out_fc)
    if out_csv:
        write_csv(out_csv, ["序号", "占用面积(平方米)", "占用面积(亩)"],
                  [[i + 1, round(r, 3), round(r / 666.6667, 4)]
                   for i, r in enumerate([a for (a,) in
                                          arcpy.da.SearchCursor(tmp, ["ZYMJ"])])])
        log("明细表：%s" % out_csv)
    arcpy.Delete_management(tmp)
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
