#!/usr/bin/env bash
# 一键：构建 → 打包 .esriAddinX → 注册安装（改完代码跑这一个脚本即可）
#
# 为什么不用 Esri 的打包 targets：它用了 CodeTaskFactory（内联 C# 任务），
# .NET Core 版 MSBuild 不支持，会报 MSB4801/MSB4036。
# 所以这里：Directory.Build.targets 覆盖掉那三个目标 → Python zipfile 自己打包 → 官方 RegisterAddIn.exe 注册。
#
# 用法：
#   ./build_addin.sh                 # 自动查找 Pro 安装位置
#   PRO_BIN=/path/to/Pro/bin ./build_addin.sh
#   PYTHON=/path/to/python ./build_addin.sh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
PROJ="$ROOT/bridge-addin"
PY="${PYTHON:-python}"

# git-bash 的 /a/... 路径直接喂给 Windows 版 Python 会被解析成 A:\a\...，必须转成原生路径
win() { cygpath -w "$1" 2>/dev/null || echo "$1"; }

echo "===== 1/4 校验 Config.daml（Pro 自带 xsd，离线）====="
# DAML 写错一个属性 → Pro 静默拒载（不报错、不写日志）。这一步能在本地先拦住。
if "$PY" "$(win "$ROOT/tools/validate_daml.py")" "$(win "$PROJ/Config.daml")" > /tmp/_daml_check.txt 2>&1; then
  tail -2 /tmp/_daml_check.txt
else
  cat /tmp/_daml_check.txt
  if grep -q "找不到 ArcGIS.Desktop.Framework.xsd\|需要 lxml" /tmp/_daml_check.txt; then
    echo "（环境缺少 lxml 或 Pro 的 xsd，跳过校验，继续构建）"
  else
    echo "❌ Config.daml 校验未通过，已中止（避免装上一个会被 Pro 静默拒载的包）"
    exit 1
  fi
fi

echo
echo "===== 2/4 构建 ====="
cd "$PROJ"
dotnet build -c Release

echo
echo "===== 3/4 打包 .esriAddinX ====="
"$PY" "$(win "$PROJ/package_addin.py")" "$(win "$PROJ")"

echo
echo "===== 4/4 注册安装 ====="
REG=""
for c in \
  "${PRO_BIN:+$PRO_BIN/RegisterAddIn.exe}" \
  "/c/Program Files/ArcGIS/Pro/bin/RegisterAddIn.exe" \
  "/d/Program Files/ArcGIS/Pro/bin/RegisterAddIn.exe" \
  "/d/Work/ArcGIS/Pro/bin/RegisterAddIn.exe" \
  $(ls -d /?/ArcGIS/Pro/bin 2>/dev/null | sed 's|^|/|;s|^/\([a-z]\)|\1|' | sed 's|$|/RegisterAddIn.exe|' | sed 's|^|/|')
do
  [ -n "$c" ] && [ -f "$c" ] && REG="$c" && break
done

if [ -z "$REG" ]; then
  echo "找不到 RegisterAddIn.exe。请用 PRO_BIN 指定 ArcGIS Pro 的 bin 目录，例如："
  echo "  PRO_BIN='D:\\ArcGIS\\Pro\\bin' ./build_addin.sh"
  echo
  echo "已生成安装包（手动安装也一样）："
  echo "  $PROJ/bin/Release/YghsBridge.esriAddinX"
  echo "  双击它，或在 Pro 里用「项目 → 加载项管理器」添加。"
  exit 1
fi

"$REG" "$(win "$PROJ/bin/Release/YghsBridge.esriAddinX")" /s
echo "已调用注册工具: $REG"

# ---------------------------------------------------------------------------
# 关键一步：清掉 Pro 的解包缓存
# Pro 把插件解包到 %LOCALAPPDATA%\ESRI\ArcGISPro\AssemblyCache\{GUID}\，
# 之后启动**直接复用该缓存** —— 只重装新包、不动缓存，Pro 加载的仍是旧 DLL
# （表现为 ping 返回的版本号不变、新功能不生效，且不报任何错）。
# 这里把缓存改名（不删除，可回滚），Pro 下次启动会重新解包。
# ---------------------------------------------------------------------------
CACHE_ROOT="$LOCALAPPDATA/ESRI/ArcGISPro/AssemblyCache"
if [ -d "$CACHE_ROOT" ]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  for d in "$CACHE_ROOT"/*; do
    [ -d "$d" ] || continue
    case "$(basename "$d")" in
      *.stale_*) continue ;;   # 已经备份过的跳过，避免层层嵌套
    esac
    # 用时间戳后缀，避免目标已存在时 mv 变成"移进目录里"
    mv "$d" "$d.stale_$STAMP" 2>/dev/null && echo "已挪走解包缓存: $(basename "$d") → $(basename "$d").stale_$STAMP"
  done
fi

echo
echo "⚠️  需要重启 ArcGIS Pro 才会加载（之后开机永久自动加载）"
echo "验证:  在 MCP 客户端里调用 arcgis_pro_status，或重启 Pro 看面板"
echo "看界面日志: Pro 里 视图 → 窗格 → YGHS Bridge"
