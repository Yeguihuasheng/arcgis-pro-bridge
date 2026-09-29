# -*- coding: utf-8 -*-
"""
图斑拓扑体检（碎面 / 重叠 / 几何错误） —— ArcGIS Pro 版

入库前给图斑做一次体检：碎面（小于阈值）、疑似重叠、几何错误三类问题，输出问题清单 CSV 并打印汇总。重叠用自合并后的要素数变化判定，属「疑似」，需人工复核后再改。
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


def main(in_fc, min_area, check_overlap, out_csv):
    if not arcpy.Exists(in_fc):
        log(u"错误：输入图层不存在 %s" % in_fc)
        return 1
    try:
        min_a = float(min_area or 0)
    except (TypeError, ValueError):
        min_a = 0.0
    rows = []
    area = area_field(in_fc)
    n = int(arcpy.GetCount_management(in_fc).getOutput(0))
    log(u"体检 %s：共 %d 个图斑" % (in_fc, n))

    # 1 碎面
    n_small = 0
    if min_a > 0:
        oid = [f.name for f in arcpy.ListFields(in_fc) if f.type == u"OID"]
        flds = (oid[:1] or [u"OID@"]) + [area]
        with arcpy.da.SearchCursor(in_fc, flds) as cur:
            for r in cur:
                a = area_value(r[-1])
                if a < min_a:
                    n_small += 1
                    rows.append([u"碎面", r[0], u"面积 %.2f 平方米，小于阈值 %s"
                                 % (a, min_a)])
    log(u"碎面：%d 个（阈值 %s 平方米）" % (n_small, min_a))

    # 2 几何错误
    chk = u"in_memory\geo_chk"
    n_geo = 0
    try:
        arcpy.CheckGeometry_management([in_fc], chk)
        fs = [f.name for f in arcpy.ListFields(chk)]
        with arcpy.da.SearchCursor(chk, fs) as cur:
            for r in cur:
                d = dict(zip(fs, r))
                n_geo += 1
                rows.append([u"几何错误",
                             d.get(u"FEATURE_ID", d.get(u"FID", u"")),
                             u"%s" % (d.get(u"PROBLEM", u""))])
        arcpy.Delete_management(chk)
    except Exception as e:
        log(u"警告：几何检查未执行（%s）" % err_text(e))
    log(u"几何错误：%d 条" % n_geo)

    # 3 疑似重叠（自合并后要素数变多即疑似存在压盖）
    n_ov = 0
    if (check_overlap or u"").strip().startswith(u"是"):
        uni = u"in_memory\geo_union"
        try:
            arcpy.Union_analysis([in_fc], uni, u"ONLY_FID")
            n_u = int(arcpy.GetCount_management(uni).getOutput(0))
            n_ov = n_u - n
            if n_ov > 0:
                rows.append([u"疑似重叠", u"", u"自合并后多出 %d 个面，需人工复核压盖位置"
                             % n_ov])
            arcpy.Delete_management(uni)
        except Exception as e:
            log(u"警告：重叠检查未执行（%s）" % err_text(e))
    log(u"疑似重叠：%s" % (u"无" if n_ov <= 0 else u"%d 处（疑似）" % n_ov))

    write_csv(out_csv, [u"问题类型", u"要素标识", u"说明"], rows)
    log(u"问题清单：%s（共 %d 条）" % (out_csv, len(rows)))
    if not rows:
        log(u"结论：未发现上述三类问题")
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
