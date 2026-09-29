# -*- coding: utf-8 -*-
"""
批量合并图层 —— ArcGIS Pro 版

把结构相同的一批图层合并成一个，常用于把分幅、分村、分批次的成果拼成一张总图。合并前会逐个检查字段是否一致，字段不一致会明确指出差异并中止，避免合并出空字段；可选择保留来源图层名，方便回溯每条数据是从哪张表来的。
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


def _field_sig(ds):
    """返回 {字段名: 类型} 用于比对结构是否一致。"""
    sig = {}
    for f in arcpy.ListFields(ds):
        if f.type in (u"OID", u"Geometry") or f.required:
            continue
        sig[f.name.upper()] = f.type
    return sig


def main(in_arg, out_fc, keep_src):
    ins = _split(in_arg)
    out_fc = (u"" if out_fc is None else unicode(out_fc)).strip()
    keep = (u"" if keep_src is None else unicode(keep_src)).strip() in (u"是", u"Y", u"y", u"1", u"True")
    if len(ins) < 2:
        log(u"错误：至少要给 2 个输入图层，当前 %d 个。" % len(ins))
        return 2
    if not out_fc:
        log(u"错误：必须填输出图层。")
        return 2
    missing = [x for x in ins if not arcpy.Exists(x)]
    if missing:
        log(u"错误：以下图层不存在 -> %s" % u"；".join(missing))
        return 1

    base_sig = _field_sig(ins[0])
    for x in ins[1:]:
        sig = _field_sig(x)
        diff_a = sorted(set(base_sig) - set(sig))
        diff_b = sorted(set(sig) - set(base_sig))
        type_diff = sorted(k for k in set(base_sig) & set(sig)
                           if base_sig[k] != sig[k])
        if diff_a or diff_b or type_diff:
            log(u"错误：%s 与 %s 结构不一致，已中止。" % (ins[0], x))
            if diff_a:
                log(u"  第一个有、它没有：%s" % u"，".join(diff_a))
            if diff_b:
                log(u"  它有、第一个没有：%s" % u"，".join(diff_b))
            if type_diff:
                log(u"  字段类型不同：%s" % u"，".join(type_diff))
            return 1

    src_field = u"SRC_LAYER"
    if keep:
        for x in ins:
            if src_field not in [f.name.upper() for f in arcpy.ListFields(x)]:
                arcpy.AddField_management(x, src_field, "TEXT", field_length=120)
        for x in ins:
            nm = os.path.splitext(os.path.basename(x))[0]
            arcpy.CalculateField_management(x, src_field, u'"%s"' % nm, "PYTHON_9.3")

    log(u"合并 %d 个图层 -> %s" % (len(ins), out_fc))
    try:
        arcpy.Merge_management(ins, out_fc)
    except Exception as e:
        log(u"错误：合并失败（%s）" % err_text(e))
        return 1
    n = int(arcpy.GetCount_management(out_fc).getOutput(0))
    log(u"完成：合并后共 %d 条记录" % n)
    for x in ins:
        log(u"  %s：%s" % (os.path.basename(x),
                           arcpy.GetCount_management(x).getOutput(0)))
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
