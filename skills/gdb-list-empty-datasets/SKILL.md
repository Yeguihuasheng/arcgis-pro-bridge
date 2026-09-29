---
name: gdb-list-empty-datasets
name_en: 检出空图层
name_zh: 检出空图层
description: 扫描工作空间找出记录数为 0 的图层，交付前清垃圾用。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 检出空图层 or similar operations.
description_en: 扫描工作空间找出记录数为 0 的图层，交付前清垃圾用。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 检出空图层 or similar operations.
description_zh: 扫描工作空间找出记录数为 0 的图层，交付前清垃圾用。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「检出空图层」或同类操作时使用。
argument-hint: <输入工作空间（GDB / 文件夹 / SDE）> <数据集类型（留空表示全部）>
argument-hint-en: <输入工作空间（GDB / 文件夹 / SDE）> <数据集类型（留空表示全部）>
argument-hint-zh: <输入工作空间（GDB / 文件夹 / SDE）> <数据集类型（留空表示全部）>
user-invocable: true
---

# 检出空图层

## 功能
扫描工作空间找出记录数为 0 的图层，交付前清垃圾用。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入工作空间（GDB / 文件夹 / SDE）
- 数据集类型（留空表示全部）
- 输出位置（GDB 要素类 / 表 / csv 路径）
- 坐标系要求：沿用当前工程

**原工具参数项**（提取自开源实现，作问询参照）：
1. 输入工作空间（GDB / 文件夹 / SDE）（原工具参数名：Workspace）
2. 数据集类型（留空表示全部）（原工具参数名：Dataset Type）

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
python scripts\run.py <输入工作空间（GDB / 文件夹 / SDE）> <数据集类型（留空表示全部）>
```
参数说明：
1. 输入工作空间（GDB / 文件夹 / SDE）（原工具参数名：Workspace）
2. 数据集类型（留空表示全部）（原工具参数名：Dataset Type）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
