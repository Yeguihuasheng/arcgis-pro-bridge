---
name: gdb-inventory-csv
name_en: 工作空间数据清单导出 CSV
name_zh: 工作空间数据清单导出 CSV
description: 把文件地理数据库/个人库/SDE 工作空间内的全部要素类与表清点成 CSV 清单（路径、要素数据集、名称、几何类型），用于交付前盘库与成果核对。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 工作空间数据清单导出 CSV or similar operations.
description_en: 把文件地理数据库/个人库/SDE 工作空间内的全部要素类与表清点成 CSV 清单（路径、要素数据集、名称、几何类型），用于交付前盘库与成果核对。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 工作空间数据清单导出 CSV or similar operations.
description_zh: 把文件地理数据库/个人库/SDE 工作空间内的全部要素类与表清点成 CSV 清单（路径、要素数据集、名称、几何类型），用于交付前盘库与成果核对。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「工作空间数据清单导出 CSV」或同类操作时使用。
argument-hint: <输入工作空间（GDB / 文件夹 / SDE）> <输出 CSV 文件路径>
argument-hint-en: <输入工作空间（GDB / 文件夹 / SDE）> <输出 CSV 文件路径>
argument-hint-zh: <输入工作空间（GDB / 文件夹 / SDE）> <输出 CSV 文件路径>
user-invocable: true
---

# 工作空间数据清单导出 CSV

## 功能
把文件地理数据库/个人库/SDE 工作空间内的全部要素类与表清点成 CSV 清单（路径、要素数据集、名称、几何类型），用于交付前盘库与成果核对。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入工作空间（GDB / 文件夹 / SDE）
- 输出 CSV 文件路径
- 输出位置（GDB 要素类 / 表 / csv 路径）
- 坐标系要求：沿用当前工程

**原工具参数项**（提取自开源实现，作问询参照）：
1. 输入工作空间（GDB / 文件夹 / SDE）（原工具参数名：Workspace）
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
python scripts\run.py <输入工作空间（GDB / 文件夹 / SDE）> <输出 CSV 文件路径>
```
参数说明：
1. 输入工作空间（GDB / 文件夹 / SDE）（原工具参数名：Workspace）
2. 输出 CSV 文件路径（原工具参数名：Output CSV File）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
