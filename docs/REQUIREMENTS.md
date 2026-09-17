# 软件环境清单（部署前对照）

> 结论先行：**最终用户只需要 ArcGIS Pro**（3.4 及以上，64 位 Windows）。
> 想用脚本/AI 驱动才需要 Python；想自己编译插件才需要 .NET SDK。**不需要** Visual Studio、不需要 conda、不需要装 arcpy。

---

## 一、按角色分：你到底要装什么

| 角色 | 必备 | 可选 | 不需要 |
|---|---|---|---|
| **A. 只用插件（面板 + 手动跑）** | ArcGIS Pro 3.4+ | — | Python、.NET SDK、Visual Studio |
| **B. 用命令行 / AI(MCP) 驱动** | ArcGIS Pro 3.4+、**Python 3.8+** | MCP 客户端（Claude Desktop、Cursor 等） | .NET SDK |
| **C. 从源码构建插件** | ArcGIS Pro 3.4+、**.NET 8 SDK**、能访问 NuGet 的网络 | Git、Git-Bash（用一键脚本时需要）、`lxml`（跑 DAML 校验时需要） | Visual Studio |

---

## 二、详细清单（含版本依据）

### 1. 操作系统

| 项 | 要求 | 依据 |
|---|---|---|
| Windows | **10 / 11，64 位** | ArcGIS Pro 只支持 64 位 Windows；插件 `PlatformTarget=x64` |
| 不建议 | Windows Server 桌面体验、ARM 版 | 未经测试 |

### 2. ArcGIS Pro

| 项 | 要求 | 说明 |
|---|---|---|
| 版本 | **3.4 及以上** | `Config.daml` 里 `desktopVersion="3.4"`；插件按 Pro 3.4 的 SDK 编译（`Esri.ArcGISPro.Extensions30 3.4.1.55405`） |
| 更低版本 | 3.2 / 3.3 需重新编译 | .NET 8 从 Pro 3.2 起；把 csproj 的包版本与 DAML 的 `desktopVersion` 改成目标版本即可 |
| **Pro 3.0 / 3.1** | ❌ 不行 | 它们用 .NET 6，加载不了 `net8.0` 程序集 |
| 许可等级 | Basic 即可（够用） | 用到扩展模块（Spatial Analyst 等）的 GP 工具时才需要对应许可，否则会报 `ERROR 000824` 之类 |
| 安装路径 | 任意 | 构建脚本会自动探测 `RegisterAddIn.exe`；探测不到时用 `PRO_BIN=<Pro>\bin ./build_addin.sh` |

### 3. .NET

| 场景 | 要求 | 说明 |
|---|---|---|
| 最终用户 | **无需安装** | ArcGIS Pro 3.4 自带 .NET 8 运行时；`.esriAddinX` 里已经是编译好的 DLL |
| 自己编译 | **.NET 8 SDK** | `dotnet --list-sdks` 应能看到 8.x；**不需要** Visual Studio |
| NuGet 访问 | 需要能拉到 `Esri.ArcGISPro.Extensions30`（约几十 MB） | 国内建议配镜像：<br>`dotnet nuget add source https://mirrors.huaweicloud.com/repository/nuget/v3/index.json -n huawei` |

### 4. Python（只有 B 类角色需要）

| 项 | 要求 | 说明 |
|---|---|---|
| 版本 | **Python 3.8+**（最低 3.7，因为用到 `sys.stdout.reconfigure`） | 任意发行版都行：官方安装包、微软商店版、Pro 自带 conda Python 亦可 |
| 第三方包 | **零依赖** | `mcp-server/` 只用标准库（socket / json / os / re / subprocess / time / uuid / zipfile） |
| **不需要 arcpy** | ✅ | 真正的 arcpy 是在 Pro 进程里跑的 —— 这正是本方案的意义 |
| 是否需要 conda | 不需要 | 别把 arcpy 装进系统 Python |
| 在 PATH 里 | MCP 客户端按 `python` 启动时必须有 | 若没有，可在 MCP 配置里写全路径，例如 `"command": "D:\\Python311\\python.exe"` |
| Pro 自带 Python（可选） | `<Pro>\bin\Python\envs\arcgispro-py3\python.exe` | 没有系统 Python 时可直接用它 |

### 5. 其他（按需）

| 软件 | 什么时候需要 | 说明 |
|---|---|---|
| **Git** | 从源码构建 / 参与开发 | 只拿 `.esriAddinX` 的话不需要 |
| **Git-Bash** | 用仓库根目录 `build_addin.sh` 一键脚本 | Windows 版 Git 自带；脚本里用到 `cygpath` |
| **lxml** | 跑 `tools/validate_daml.py`（改 DAML 前离线校验） | `pip install lxml`；不装也不影响插件运行 |
| **MCP 客户端** | 想让 AI 直接操作 Pro | Claude Desktop / Cursor / 其它支持 MCP 的客户端；配置见主 README |
| 浏览器 | 打开问题反馈里的链接 | 系统默认浏览器即可 |

### 6. 网络与端口

| 项 | 说明 |
|---|---|
| 网络 | 运行期**完全离线**（只连本机回环）；只有编译/装包时才需要外网 |
| 端口 | 默认 **18750**，被占用自动顺延到 **18761**；实际端口写在 `%LOCALAPPDATA%\YghsBridge\port.txt` |
| 监听地址 | 只绑 `127.0.0.1` → 不暴露到局域网、通常不触发防火墙弹窗 |
| 跨机使用 | ❗ 不支持开箱即用；需自行做 SSH 隧道，**不要**改成 `0.0.0.0`（等于开放任意代码执行） |

### 7. 权限与安全软件

| 项 | 说明 |
|---|---|
| 管理员权限 | **不需要**。插件装到 `%USERPROFILE%\Documents\ArcGIS\AddIns\` |
| 杀软 / EDR | 可能拦截两件事：① 从 `%TEMP%` 解包并执行 `.pyt`；② 监听回环端口。**建议加白名单**：`%TEMP%\YghsBridge*`、`%~dp0YghsBridge.esriAddinX` |
| 磁盘 | 插件本体约 30 KB；日志与临时脚本在 `%TEMP%`，量级 MB |

---

## 三、一分钟自检脚本

把下面这段存成 `check_env.py` 跑一遍，逐项打印是否满足：

```python
# -*- coding: utf-8 -*-
"""部署环境自检（不依赖第三方库）。"""
import glob, os, platform, shutil, subprocess, sys

def line(ok, name, detail=""):
    print("%s %-28s %s" % ("[ OK ]" if ok else "[FAIL]", name, detail))

print("=== YghsBridge 环境自检 ===\n")

# 1) 系统
w = platform.system() == "Windows"
line(w, "Windows", platform.platform())
line(platform.machine().endswith("64"), "64 位系统", platform.machine())

# 2) ArcGIS Pro
pro = []
for pat in (r"C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe", r"D:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe",
            r"C:\ArcGIS\Pro\bin\ArcGISPro.exe", r"D:\Work\ArcGIS\Pro\bin\ArcGISPro.exe"):
    if os.path.exists(pat):
        pro.append(pat)
for d in "CDEFGH":
    pro += glob.glob("%s:\\*ArcGIS*\\Pro\\bin\\ArcGISPro.exe" % d)
line(bool(pro), "ArcGIS Pro", pro[0] if pro else "未找到（可手填）")

reg = [p for p in pro if os.path.exists(os.path.join(os.path.dirname(p), "RegisterAddIn.exe"))]
line(bool(reg), "RegisterAddIn.exe", os.path.dirname(reg[0]) if reg else "需设 PRO_BIN")

# 3) 已安装插件
addin = os.path.join(os.environ.get("USERPROFILE", ""), r"Documents\ArcGIS\AddIns\ArcGISPro")
found = glob.glob(os.path.join(addin, "*", "YghsBridge.esriAddinX"))
line(bool(found), "插件已安装", found[0] if found else "尚未安装")

# 4) Python
line(sys.version_info >= (3, 8), "Python >= 3.8",
     "%d.%d.%d (%s)" % (sys.version_info[:3] + (sys.executable,)))
for m in ("socket", "json", "zipfile", "subprocess"):
    try:
        __import__(m)
    except Exception as e:
        line(False, "标准库 " + m, str(e))

# 5) .NET SDK（只有自己编译才需要）
try:
    out = subprocess.run(["dotnet", "--list-sdks"], capture_output=True, text=True, timeout=20)
    sdk = [l for l in out.stdout.splitlines() if l.startswith("8.")]
    line(bool(sdk), ".NET 8 SDK", (sdk[0] if sdk else "未安装（仅编译需要）"))
except Exception:
    line(False, ".NET 8 SDK", "未安装（仅编译需要）")

# 6) 端口与端口文件
import socket
pf = os.path.join(os.environ.get("LOCALAPPDATA", ""), "YghsBridge", "port.txt")
port = 18750
if os.path.exists(pf):
    try:
        port = int(open(pf).read().strip())
    except Exception:
        pass
line(os.path.exists(pf), "端口文件", pf if os.path.exists(pf) else "（Pro 未启动过插件时不存在）")
s = socket.socket()
try:
    s.settimeout(3)
    s.connect(("127.0.0.1", port))
    line(True, "插件在线", "127.0.0.1:%d" % port)
except Exception as e:
    line(False, "插件在线", "连不上 %d：%s（Pro 没开 / 插件没加载 / 端口被占）" % (port, e))
finally:
    s.close()

print("\n提示：B 类角色（脚本/AI 驱动）只需 Python；C 类（自己编译）才需要 .NET SDK。")
```

---

## 四、常见"环境不对"的症状对照

| 症状 | 大概率原因 |
|---|---|
| 双击 `.esriAddinX` 提示无法安装 / 装完 Pro 里没有 YghsBridge 标签页 | Pro 版本低于 3.4，或装了但**没重启 Pro** |
| 装了新版但功能没变、版本号还是旧的 | Pro 的 **AssemblyCache** 缓存（见 `docs/DEPLOYMENT.md` 第四节） |
| `[连不上插件]` | Pro 没开；或插件没加载；或端口被占（看 `%LOCALAPPDATA%\YghsBridge\port.txt`） |
| MCP 客户端报启动失败 | 配置里的 `python` 不在 PATH —— 改成 Python 全路径 |
| 中文结果乱码（MCP） | 客户端不是最新版（v1.10 起服务端强制 UTF-8 stdio） |
| 面板里没有新内容 | 面板是懒创建的，需要**从菜单打开过一次** |
| 执行 GP 报许可错误 | Pro 许可等级不够 / 缺扩展模块许可 |
