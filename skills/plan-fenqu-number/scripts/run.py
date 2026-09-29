# -*- coding: utf-8 -*-
"""
用途分区编号生成 —— ArcGIS Pro 版

按空间位置（自西向东、自北向南）给用途分区图斑生成连续编号并写入字段，同时可输出分区面积表。对应原工具箱的「用途分区编号生成 / 用途分区规划图生成」。
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

def main(fq_fc, code_field, prefix, out_csv):
    """按位置排序生成连续分区编号。"""
    if not arcpy.Exists(fq_fc):
        log("错误：图层不存在 %s" % fq_fc)
        return 2
    code_field = code_field or "FQBH"
    prefix = prefix or ""
    ensure_field(fq_fc, code_field, "TEXT", "分区编号", 30)
    ensure_field(fq_fc, "MJ", "DOUBLE", "面积(平方米)")
    arcpy.CalculateField_management(fq_fc, "MJ", area_expr(fq_fc), "PYTHON_9.3")

    feats = []
    with arcpy.da.SearchCursor(fq_fc, ["OID@", "SHAPE@XY", "MJ"]) as cur:
        for oid, xy, mj in cur:
            x, y = xy[0], xy[1]
            feats.append((round(-y, 1), x, oid, mj or 0))
    feats.sort()

    kv = {}
    rows = []
    for i, (_ny, _x, oid, mj) in enumerate(feats, start=1):
        code = "%s%02d" % (prefix, i)
        kv[oid] = code
        rows.append([code, round(mj, 3), round(mj / 666.6667, 4)])
    with arcpy.da.UpdateCursor(fq_fc, ["OID@", code_field]) as cur:
        for row in cur:
            if row[0] in kv:
                row[1] = kv[row[0]]
                cur.updateRow(row)
    log("已生成 %d 个分区编号（字段 %s）" % (len(kv), code_field))
    if out_csv:
        write_csv(out_csv, ["分区编号", "面积(平方米)", "面积(亩)"], rows)
        log("面积表：%s" % out_csv)
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
