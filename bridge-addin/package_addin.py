# -*- coding: utf-8 -*-
"""把 dotnet 构建产物打成 .esriAddinX。

⚠️ 包内容必须严格对齐「已验证可用的 Pro 3.4 插件」（CLI-Anything-Arcgis-Pro 的 live-bridge）：
    Config.daml                 （包根）
    Install/YghsBridge.dll
    Install/YghsBridge.pdb
    —— 就这三样，多一个 deps.json 都可能让加载器解析失败（它会把 ArcGIS.* 指向 NuGet 的 ref 程序集）。

⚠️ Config.daml 的 defaultAssembly 必须带 .dll 扩展名。

用法: python package_addin.py <项目目录>
"""
import os
import sys
import zipfile

proj = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
outdir = os.path.join(proj, "bin", "Release")
name = "YghsBridge"
target = os.path.join(outdir, name + ".esriAddinX")

daml = os.path.join(proj, "Config.daml")
if not os.path.exists(daml):
    print("缺少:", daml)
    raise SystemExit(1)

dll = os.path.join(outdir, name + ".dll")
if not os.path.exists(dll):
    print("缺少构建产物:", dll)
    raise SystemExit(1)

files = [
    (daml, "Config.daml"),
    (dll, "Install/" + name + ".dll"),
]
pdb = os.path.join(outdir, name + ".pdb")
if os.path.exists(pdb):
    files.append((pdb, "Install/" + name + ".pdb"))

# 图标等资源：Images/ 下的 PNG 按原相对路径进包（纯资源，不影响加载器程序集解析）
# 排除 *384* 之类的大尺寸底档 —— 包里只需要实际引用的 16/32 图标
imgdir = os.path.join(proj, "Images")
if os.path.isdir(imgdir):
    for fn in sorted(os.listdir(imgdir)):
        if fn.lower().endswith(".png") and "384" not in fn:
            files.append((os.path.join(imgdir, fn), "Images/" + fn))

# 直接覆盖写：zipfile 的 "w" 模式自身会截断（沙箱里 os.remove 会抛 SAFE_DELETE_FAIL_CLOSED）
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
    for full, rel in files:
        z.write(full, rel)
        print("  + %-30s %8d 字节" % (rel, os.path.getsize(full)))

# 校验 defaultAssembly（必须带 .dll）
with open(daml, "r", encoding="utf-8-sig") as f:
    daml_txt = f.read()
if 'defaultAssembly="%s.dll"' % name not in daml_txt:
    print('!! Config.daml 的 defaultAssembly 应为 "%s.dll"（带扩展名）' % name)
    raise SystemExit(1)

print("\n已生成:", target, os.path.getsize(target), "字节")
print("包内结构:")
with zipfile.ZipFile(target) as z:
    for n in z.namelist():
        print("   ", n)
