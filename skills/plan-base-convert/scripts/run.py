# -*- coding: utf-8 -*-
"""
三调基数转换（DLBM→用地用海） —— ArcGIS Pro 版

按《国土空间调查、规划、用途管制用地用海分类指南》的衔接关系，把三调地类图斑的DLBM 编码换算为用地用海分类，一次写入：一级代码、一级名称、分类代码、分类名称。一对多需要细分的编码（如 05H1、08H2）会单独报出来，提醒人工判定。

口径提醒（重要）：带 H 与多义编码（05H1、08H1、08H2、0810A 等）在各省细则里归属并不一致，例如《安徽省村庄规划编制指南》附录D 把 05H1 部分归入「城镇社区服务设施用地」「农村社区服务设施用地」。本表按常用衔接关系给出，跑完必须拿当地指南复核报出来的待细分清单，不能直接当成果交。
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

def main(in_fc, out_fc, code_field, keep_only):
    """DLBM -> 用地用海一级/二级分类。"""
    code_field = code_field or "DLBM"
    keep_only = (keep_only or "是").strip() != "否"
    if not arcpy.Exists(in_fc):
        log("错误：输入图层不存在 %s" % in_fc)
        return 2
    names = [f.name for f in arcpy.ListFields(in_fc)]
    if code_field not in names:
        log("错误：图层里没有字段 %s，现有字段：%s" % (code_field, ",".join(names[:12])))
        return 2

    tmp = os.path.join("in_memory", "base_convert")
    if arcpy.Exists(tmp):
        arcpy.Delete_management(tmp)
    arcpy.CopyFeatures_management(in_fc, tmp)
    if keep_only:
        keep = set([code_field, "DLMC"])
        drop = [f.name for f in arcpy.ListFields(tmp)
                if f.name not in keep and not f.required and f.type not in ("OID", "Geometry")]
        if drop:
            arcpy.DeleteField_management(tmp, drop)

    v3 = _MAP["V3_TO_YDYH"]
    yd_name = _MAP["YDYH_NAME"]
    ensure_field(tmp, "YDYHFLYJDM", "TEXT", "用地用海分类一级代码", 20)
    ensure_field(tmp, "YDYHFLYJMC", "TEXT", "用地用海分类一级名称", 60)
    ensure_field(tmp, "YDYHFLDM", "TEXT", "用地用海分类代码", 20)
    ensure_field(tmp, "YDYHFLMC", "TEXT", "用地用海分类名称", 60)

    flds = [code_field, "YDYHFLYJDM", "YDYHFLYJMC", "YDYHFLDM", "YDYHFLMC"]
    hit = 0
    miss = {}
    with arcpy.da.UpdateCursor(tmp, flds) as cur:
        for row in cur:
            code = (row[0] or "").strip()
            if not code:
                continue
            yd = v3.get(code) or v3.get(code.upper())
            if not yd:
                miss[code] = miss.get(code, 0) + 1
                continue
            l1 = yd[:2]
            row[1] = l1
            row[2] = yd_name.get(l1, "")
            row[3] = yd
            row[4] = yd_name.get(yd, yd_name.get(l1, ""))
            cur.updateRow(row)
            hit += 1
    if arcpy.Exists(out_fc):
        arcpy.Delete_management(out_fc)
    arcpy.CopyFeatures_management(tmp, out_fc)
    arcpy.Delete_management(tmp)

    log("完成：匹配 %d 个图斑，未匹配 %d 种编码" % (hit, len(miss)))
    if miss:
        for c in sorted(miss):
            log("  待人工细分：DLBM=%s（%d 个图斑）" % (c, miss[c]))
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
