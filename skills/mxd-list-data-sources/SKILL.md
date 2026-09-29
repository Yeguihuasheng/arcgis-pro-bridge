---
name: mxd-list-data-sources
name_en: 列出 MXD 数据源清单
name_zh: 列出 MXD 数据源清单
description: 逐个图层列出地图文档的数据源路径（可整文件夹扫描），用于交付前的断链检查与数据源台账。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 列出 MXD 数据源清单 or similar operations.
description_en: 逐个图层列出地图文档的数据源路径（可整文件夹扫描），用于交付前的断链检查与数据源台账。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 列出 MXD 数据源清单 or similar operations.
description_zh: 逐个图层列出地图文档的数据源路径（可整文件夹扫描），用于交付前的断链检查与数据源台账。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「列出 MXD 数据源清单」或同类操作时使用。
argument-hint: <输入 MXD 地图文档（可多个）> <输出 CSV 文件路径>
argument-hint-en: <输入 MXD 地图文档（可多个）> <输出 CSV 文件路径>
argument-hint-zh: <输入 MXD 地图文档（可多个）> <输出 CSV 文件路径>
user-invocable: true
---

# 列出 MXD 数据源清单

## 功能
逐个图层列出地图文档的数据源路径（可整文件夹扫描），用于交付前的断链检查与数据源台账。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入 MXD 地图文档（可多个）
- 输出 CSV 文件路径
- 输出位置（GDB 要素类 / 表 / csv 路径）
- 坐标系要求：沿用当前工程

**原工具参数项**（提取自开源实现，作问询参照）：
1. 输入 MXD 地图文档（可多个）（原工具参数名：Input MXDs）
2. 输出 CSV 文件路径（原工具参数名：Output CSV File）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按上表顺序传入）。
运行环境：ArcGIS Pro

## 执行后复核
- 读回输出的行数/字段值或打开结果文件抽查 3 项；
- 报错时看 traceback 定位到具体参数。

## 详细说明
本技能抽取自社区开源工具箱的单个工具类，逻辑与参数保持原实现。

## 参数与调用
```bat
python scripts\run.py <输入 MXD 地图文档（可多个）> <输出 CSV 文件路径>
```
参数说明：
1. 输入 MXD 地图文档（可多个）（原工具参数名：Input MXDs）
2. 输出 CSV 文件路径（原工具参数名：Output CSV File）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
