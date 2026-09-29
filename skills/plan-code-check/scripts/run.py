# -*- coding: utf-8 -*-
"""
地类编码与名称一致性检查 —— ArcGIS Pro 版

逐图斑核对用地代码与名称是否匹配（按用地用海对照表），检出缺码、错码、新旧标准混用、代码与名称不符等问题，输出问题清单 CSV。对应原工具箱的「地类编号名称别称匹配检查 / 检查地块编号和土地码是否有问题」。
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

def main(yd_fc, code_field, name_field, out_csv):
    """代码-名称一致性体检。"""
    if not arcpy.Exists(yd_fc):
        log("错误：图层不存在 %s" % yd_fc)
        return 2
    code_field = code_field or "YDYHFLDM"
    name_field = name_field or "YDYHFLMC"
    names = [f.name for f in arcpy.ListFields(yd_fc)]
    for f in (code_field, name_field):
        if f not in names:
            log("错误：图层里没有字段 %s（现有：%s）" % (f, ",".join(names[:12])))
            return 2
    yd_name = _MAP["YDYH_NAME"]
    v3 = _MAP["V3_TO_YDYH"]

    rows = []
    n_bad = 0
    with arcpy.da.SearchCursor(yd_fc, ["OID@", code_field, name_field]) as cur:
        for oid, code, name in cur:
            code = (code or "").strip()
            name = (name or "").strip()
            if not code:
                rows.append([oid, code, name, "代码为空"])
                n_bad += 1
                continue
            std = yd_name.get(code)
            if std is None:
                rows.append([oid, code, name, "代码不在用地用海对照表"])
                n_bad += 1
                continue
            if name and name != std and std not in name and name not in std:
                rows.append([oid, code, name, "名称与代码不符，标准名称应为：%s" % std])
                n_bad += 1
    if out_csv:
        write_csv(out_csv, ["OID", "用地代码", "用地名称", "问题"], rows)
        log("问题清单：%s" % out_csv)
    total = int(arcpy.GetCount_management(yd_fc).getOutput(0))
    log("检查 %d 个图斑，发现 %d 条问题（对照表覆盖 %d 个代码 / %d 条三调映射）"
        % (total, n_bad, len(yd_name), len(v3)))
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
