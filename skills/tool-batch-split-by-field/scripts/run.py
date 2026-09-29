# -*- coding: utf-8 -*-
"""
按字段值拆分图层 —— ArcGIS Pro 版

按某个字段的取值把一个图层拆成多个图层，每个取值导出一份（如按行政村名、按用地大类、按批次号拆分）。可自定义输出名前缀，导出后汇报每个取值的要素数，空值会单独归到「空值」一组并提示。
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

_UNSAFE = u"\\/:*?\"<>| "


def _safe(s):
    s = u"" if s is None else unicode(s)
    for ch in _UNSAFE:
        s = s.replace(ch, u"_")
    return s.strip(u"_") or u"空值"


def main(in_fc, field, out_ws, prefix):
    field = (u"" if field is None else unicode(field)).strip()
    out_ws = (u"" if out_ws is None else unicode(out_ws)).strip()
    prefix = (u"" if prefix is None else unicode(prefix)).strip()
    if not arcpy.Exists(in_fc):
        log(u"错误：输入图层不存在 %s" % in_fc)
        return 1
    if not arcpy.Exists(out_ws):
        log(u"错误：输出工作空间不存在 %s" % out_ws)
        return 1
    names = [f.name for f in arcpy.ListFields(in_fc)]
    if field not in names:
        log(u"错误：图层里没有字段「%s」。可用字段：%s"
            % (field, u"，".join(names)))
        return 1

    vals = {}
    with arcpy.da.SearchCursor(in_fc, [field]) as cur:
        for (v,) in cur:
            k = u"" if v is None else unicode(v).strip()
            vals[k] = vals.get(k, 0) + 1
    if not vals:
        log(u"提示：图层没有记录。")
        return 0

    log(u"待拆分：%d 个取值" % len(vals))
    ok_n = 0
    null_n = 0
    for v, cnt in sorted(vals.items()):
        tag = _safe(v)
        out_name = (u"%s_%s" % (prefix, tag)) if prefix else tag
        if v == u"":
            null_n += cnt
        where = u'%s IS NULL' % field if v == u"" else None
        try:
            if v == u"":
                arcpy.Select_analysis(in_fc, os.path.join(out_ws, out_name), where)
            else:
                q = u'"%s" = \'%s\'' % (field, v.replace(u"'", u"''"))
                arcpy.Select_analysis(in_fc, os.path.join(out_ws, out_name), q)
        except Exception as e:
            log(u"  失败：%s（%s）" % (out_name, err_text(e)))
            continue
        ok_n += 1
        log(u"  %s：%d 个要素" % (out_name, cnt))
    log(u"完成：拆出 %d 个图层，共 %d 条记录"
        % (ok_n, int(arcpy.GetCount_management(in_fc).getOutput(0))))
    if null_n:
        log(u"提醒：有 %d 条记录的拆分字段为空，已归入「空值」图层，请核对。" % null_n)
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
