# -*- coding: utf-8 -*-
"""
用地用海分类统计表 —— ArcGIS Pro 版

按用地用海分类代码汇总图斑数与面积，输出一张表：分类代码、分类名称、图斑数、平方米 / 亩 / 公顷、占比。可选择「按一级类汇总」只看到大类，也可以按二级类明细。面积自动按坐标系切换测地面积，避免在地理坐标系下算成平方度。
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


def _load_map():
    """加载技能根目录下 resources/ydyh_map.py（exec 方式，避免包路径依赖）。

    __file__ 是 scripts/run.py，资源在上一层，所以要取两级 dirname。
    """
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(here, "resources", "ydyh_map.py")
    ns = {}
    src = io.open(p, encoding="utf-8").read()
    exec(compile(src.encode("utf-8") if sys.version_info[0] < 3 else src,
                 p, "exec"), ns)
    return ns


_MAP = _load_map()


def main(in_fc, code_field, out_csv, by_top):
    if not arcpy.Exists(in_fc):
        log(u"错误：输入图层不存在 %s" % in_fc)
        return 1
    names = [f.name for f in arcpy.ListFields(in_fc)]
    if code_field not in names:
        log(u"错误：图层里没有字段 %s，现有字段：%s"
            % (code_field, u",".join(names[:12])))
        return 1
    area = area_field(in_fc)
    agg = {}
    total = 0.0
    n = 0
    with arcpy.da.SearchCursor(in_fc, [code_field, area]) as cur:
        for code, a in cur:
            n += 1
            a = area_value(a)
            total += a
            code = (u"%s" % (code or u"")).strip()
            key = code[:2] if (by_top or u"").strip().startswith(u"是") else code
            s = agg.setdefault(key, [0, 0.0])
            s[0] += 1
            s[1] += a
    yd_name = _MAP["YDYH_NAME"]
    rows = []
    for k in sorted(agg):
        cnt, a = agg[k]
        pct = (u"%.2f%%" % (a / total * 100.0)) if total else u""
        rows.append([k, yd_name.get(k, u""), cnt, round(a, 2),
                     round(a / 666.6666667, 4), round(a / 10000.0, 6), pct])
    write_csv(out_csv,
              [u"分类代码", u"分类名称", u"图斑数", u"面积_平方米",
               u"面积_亩", u"面积_公顷", u"占比"],
              rows)
    log(u"统计完成：%d 个图斑，%d 个分类，总面积 %.2f 平方米" % (n, len(rows), total))
    log(u"统计表：%s" % out_csv)
    for r in rows[:15]:
        log(u"  %s %s %s个 %.2f平方米" % (r[0], r[1], r[2], r[3]))
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
