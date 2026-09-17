# -*- coding: utf-8 -*-
"""用 ArcGIS Pro 自带的 xsd 离线校验 Config.daml —— 改 DAML 之前先跑这个。

为什么需要：DAML 里写错一个属性或元素位置，Pro 会**静默拒载**整个插件
（不报错、不写日志、加载项管理器里也不标红），只能靠"改了→重装→重启"试错。
用这个脚本可以在本地先查出问题。

用法：
    python tools/validate_daml.py                       # 校验 bridge-addin/Config.daml
    python tools/validate_daml.py 路径/Config.daml
    python tools/validate_daml.py --xsd "D:\\ArcGIS\\Pro\\bin\\ArcGIS.Desktop.Framework.xsd"

依赖：lxml（pip install lxml）。默认在常见位置查找 Pro 安装目录。
"""
import os
import re
import sys

try:
    from lxml import etree
except ImportError:
    print("需要 lxml：pip install lxml")
    raise SystemExit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DAML = os.path.join(os.path.dirname(HERE), "bridge-addin", "Config.daml")

XSD_CANDIDATES = [
    r"C:\Program Files\ArcGIS\Pro\bin\ArcGIS.Desktop.Framework.xsd",
    r"D:\Program Files\ArcGIS\Pro\bin\ArcGIS.Desktop.Framework.xsd",
    r"D:\Work\ArcGIS\Pro\bin\ArcGIS.Desktop.Framework.xsd",
    r"C:\ArcGIS\Pro\bin\ArcGIS.Desktop.Framework.xsd",
]


def find_xsd():
    for c in XSD_CANDIDATES:
        if os.path.exists(c):
            return c
    for drive in "CDEFGH":
        c = "%s:\\Program Files\\ArcGIS\\Pro\\bin\\ArcGIS.Desktop.Framework.xsd" % drive
        if os.path.exists(c):
            return c
    return None


def main():
    args = sys.argv[1:]
    xsd_path = None
    if "--xsd" in args:
        i = args.index("--xsd")
        xsd_path = args[i + 1]
        del args[i:i + 2]
    daml = args[0] if args else DEFAULT_DAML
    xsd_path = xsd_path or find_xsd()

    if not xsd_path or not os.path.exists(xsd_path):
        print("找不到 ArcGIS.Desktop.Framework.xsd，请用 --xsd 指定 Pro 的 bin 目录下的该文件")
        return 2
    if not os.path.exists(daml):
        print("找不到 DAML:", daml)
        return 2

    print("xsd :", xsd_path)
    print("daml:", daml)

    raw = open(xsd_path, encoding="utf-8-sig").read()

    # Pro 自带的 xsd 引用了若干未在本文件中定义的类型（如 CT_ExtensionConfig），
    # 直接编译会失败。这里迭代剔除引用未定义类型的 <xs:element .../>，直到能编译为止。
    removed = []
    for _ in range(50):
        try:
            schema = etree.XMLSchema(etree.fromstring(raw.encode("utf-8")))
            break
        except etree.XMLSchemaParseError as e:
            m = re.search(r"element decl\. '\{[^}]*\}([A-Za-z0-9_]+)'", str(e))
            if not m:
                print("无法编译 schema:", e)
                return 2
            name = m.group(1)
            pat = re.compile(r'\n\s*<xs:element name="%s"[^>]*/>' % re.escape(name))
            if not pat.search(raw):
                print("找不到要剔除的元素声明:", name)
                return 2
            raw = pat.sub("", raw, count=1)
            removed.append(name)

    if removed:
        print("（为编译 schema 剔除了 %d 个引用外部类型的元素：%s）" % (len(removed), ", ".join(removed)))

    doc = etree.parse(daml)
    ok = schema.validate(doc)
    print()
    if ok:
        print("DAML 校验：通过 ✅")
        return 0
    print("DAML 校验：失败 ❌")
    for e in schema.error_log:
        print("  行 %s: %s" % (e.line, e.message))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
