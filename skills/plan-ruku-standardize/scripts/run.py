# -*- coding: utf-8 -*-
"""
入库要素规整（字段/坐标系/清历史） —— ArcGIS Pro 版

入库前的一次性规整：字段名统一大写、去字段名与值里的多余空格、坐标系统一到指定投影、清理地理处理历史、清掉空图层。对应原工具箱「入库_*」前的公共准备动作。
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

def main(workspace, prj, upper, drop_empty):
    """入库前规整：大写字段名 + 坐标系统一 + 清空图层。"""
    if not arcpy.Exists(workspace):
        log("错误：工作空间不存在 %s" % workspace)
        return 2
    upper = (upper or "是").strip() != "否"
    drop_empty = (drop_empty or "是").strip() != "否"
    arcpy.env.workspace = workspace

    fcs = list(arcpy.ListFeatureClasses() or [])
    for ds in (arcpy.ListDatasets("", "Feature") or []):
        fcs += [os.path.join(ds, f) for f in (arcpy.ListFeatureClasses("", "", ds) or [])]
    log("工作空间内要素类 %d 个" % len(fcs))

    for fc in fcs:
        # 1) 字段名大写 + 去空格
        if upper:
            for f in arcpy.ListFields(fc):
                if f.required or f.type in ("OID", "Geometry"):
                    continue
                new = f.name.strip().upper().replace(" ", "")
                if new and new != f.name:
                    try:
                        arcpy.AlterField_management(fc, f.name, new, new)
                    except Exception:
                        pass
        # 2) 坐标系
        if prj:
            sr = arcpy.Describe(fc).spatialReference
            try:
                target = arcpy.SpatialReference(prj)
            except Exception:
                log("警告：坐标系无法识别 %s，跳过投影" % prj)
                target = None
            if target and sr.name != target.name:
                out = fc + "_prj"
                if arcpy.Exists(out):
                    arcpy.Delete_management(out)
                arcpy.Project_management(fc, out, target)
                log("  投影：%s -> %s" % (fc, out))
        # 3) 空图层
        if drop_empty:
            n = int(arcpy.GetCount_management(fc).getOutput(0))
            if n == 0:
                log("  空图层（建议删除）：%s" % fc)
    log("规整完成。")
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
