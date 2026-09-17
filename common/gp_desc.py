# -*- coding: utf-8 -*-
"""把 GP 工具调用翻译成"人话"，用于面板 / 通知 / 日志里的可读提示。

给一个工具名和参数，返回三段中文：
    desc    —— 开始做什么（例：给 GHFQ 添加文本字段 GHGHYDYD）
    okdesc  —— 成功后说什么（例：GHGHYDYD 文本字段 已添加成功）
    faildesc—— 失败后说什么（例：GHGHYDYD 文本字段 添加失败）

未知工具退回通用文案（"执行 xxx" / "xxx 执行完成"），不会报错。
"""
import os

# 字段类型代码 → 中文
TYPE_CN = {
    "TEXT": "文本", "STRING": "文本", "CHAR": "文本",
    "DOUBLE": "双精度", "FLOAT": "浮点", "SINGLE": "浮点",
    "LONG": "长整型", "SHORT": "短整型", "INTEGER": "整型", "BIGINTEGER": "长整型",
    "DATE": "日期", "BLOB": "二进制", "RASTER": "栅格", "GUID": "GUID",
}


def _name(path):
    """从数据源路径里取一个短名字（去掉扩展名 / 到 .gdb 后的要素类名）。"""
    if not path:
        return "数据"
    p = str(path).replace("/", "\\").rstrip("\\")
    if ".gdb\\" in p.lower():
        # …\x.gdb\图层名 → 图层名
        return p.split("\\")[-1]
    base = os.path.basename(p)
    return os.path.splitext(base)[0] or base


def _type_cn(t):
    return TYPE_CN.get((t or "").strip().upper(), (t or "").strip() or "未知类型")


def describe_gp(tool, args):
    """返回 (desc, okdesc, faildesc)。args 为字符串列表。"""
    t = (tool or "").strip()
    tl = t.lower()
    short = t.split(".")[-1] if "." in t else t
    a = list(args or [])

    def get(i, default=""):
        return a[i] if len(a) > i and a[i] is not None else default

    # ---- 字段类 ----
    if tl.endswith("management.addfield"):
        fc, fld, typ = _name(get(0)), get(1, "字段"), _type_cn(get(2))
        return ("给 %s 添加%s字段 %s" % (fc, typ, fld),
                "%s %s字段 已添加成功" % (fld, typ),
                "%s %s字段 添加失败" % (fld, typ))

    if tl.endswith("management.deletefield"):
        fc, flds = _name(get(0)), (get(1).replace(";", "、") or "字段")
        return ("从 %s 删除字段 %s" % (fc, flds),
                "%s 字段 已删除" % flds,
                "%s 字段 删除失败" % flds)

    if tl.endswith("management.alterfield"):
        fc, fld = _name(get(0)), get(1, "字段")
        new = get(2) or get(3)
        if new and new != get(1):
            return ("在 %s 上重命名字段 %s → %s" % (fc, fld, new),
                    "%s 字段 已重命名为 %s" % (fld, new),
                    "%s 字段 重命名失败" % fld)
        return ("修改 %s 的字段 %s" % (fc, fld), "%s 字段 已修改" % fld, "%s 字段 修改失败" % fld)

    if tl.endswith("management.calculatefield"):
        fc, fld, expr = _name(get(0)), get(1, "字段"), get(2)
        return ("给 %s 的 %s 字段写值：%s" % (fc, fld, expr or "(空表达式)"),
                "%s 字段 已写入成功" % fld,
                "%s 字段 写入失败" % fld)

    if tl.endswith("management.addfields"):
        fc = _name(get(0))
        return ("给 %s 批量添加字段" % fc, "%s 的字段 已批量添加成功" % fc, "%s 字段批量添加失败" % fc)

    # ---- 要素类 / 数据 ----
    if tl.endswith("management.createfeatureclass"):
        out_name, geo = get(1, "要素类"), get(2)
        return ("创建要素类 %s%s" % (out_name, ("（%s）" % geo) if geo else ""),
                "%s 要素类 已创建" % out_name,
                "%s 要素类 创建失败" % out_name)

    if tl.endswith(("conversion.featureclasstofeatureclass", "conversion.featureclasstoshapefile")):
        src, dst, name = _name(get(0)), get(1), get(2)
        return ("把 %s 导出到 %s\\%s" % (src, dst, name),
                "%s 已导出成功" % (name or src),
                "%s 导出失败" % (name or src))

    if tl.endswith("management.copyfeatures"):
        return ("复制要素 %s → %s" % (_name(get(0)), _name(get(1))),
                "%s 已复制成功" % _name(get(1)),
                "%s 复制失败" % _name(get(1)))

    if tl.endswith("management.delete"):
        return ("删除 %s" % _name(get(0)), "%s 已删除" % _name(get(0)), "%s 删除失败" % _name(get(0)))

    if tl.endswith("management.rename"):
        return ("重命名 %s → %s" % (_name(get(0)), _name(get(1))),
                "已重命名为 %s" % _name(get(1)),
                "重命名失败")

    if tl.endswith(("management.project", "management.projectraster")):
        return ("投影 %s → %s" % (_name(get(0)), _name(get(1))),
                "%s 投影完成" % _name(get(1)),
                "%s 投影失败" % _name(get(1)))

    if tl.endswith("management.createfilegdb"):
        return ("创建文件地理数据库 %s" % _name(get(1)),
                "%s 数据库 已创建" % _name(get(1)),
                "%s 数据库 创建失败" % _name(get(1)))

    # ---- 分析类 ----
    if tl.endswith("analysis.buffer"):
        return ("对 %s 做缓冲区分析" % _name(get(0)), "缓冲区分析 已完成", "缓冲区分析 失败")
    if tl.endswith("analysis.clip"):
        return ("用 %s 裁剪 %s" % (_name(get(1)), _name(get(0))), "裁剪 已完成", "裁剪 失败")
    if tl.endswith("analysis.intersect"):
        return ("叠加求交 %s" % "、".join(_name(x) for x in a[:3] if x), "叠加求交 已完成", "叠加求交 失败")
    if tl.endswith("analysis.dissolve"):
        return ("融合 %s" % _name(get(0)), "融合 已完成", "融合 失败")
    if tl.endswith(("analysis.select", "management.selectlayerbyattribute")):
        return ("按条件选择要素", "要素选择 已完成", "要素选择 失败")
    if tl.endswith("management.addjoin"):
        return ("连接 %s 与 %s" % (_name(get(0)), _name(get(1))), "表连接 已完成", "表连接 失败")
    if tl.endswith("management.addspatialindex"):
        return ("给 %s 建空间索引" % _name(get(0)), "%s 空间索引 已建立" % _name(get(0)), "空间索引 建立失败")

    # ---- 只读 ----
    if tl.endswith("management.getcount"):
        return ("统计 %s 的要素数" % _name(get(0)), "%s 要素数统计 完成" % _name(get(0)), "要素数统计 失败")
    if tl.endswith(("management.exists", "management.test")):
        return ("检查 %s 是否存在" % _name(get(0)), "存在性检查 完成", "存在性检查 失败")

    # ---- 通用兜底 ----
    return ("执行 %s" % short, "%s 执行完成" % short, "%s 执行失败" % short)

