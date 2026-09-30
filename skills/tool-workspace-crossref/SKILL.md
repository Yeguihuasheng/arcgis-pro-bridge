---
name: tool-workspace-crossref
name_en: 生成工作空间要素交叉引用表
name_zh: 生成工作空间要素交叉引用表
description: 扫描工作空间，建立数据集与要素之间的交叉引用（被哪些图层/关系引用）清单，用于迁移、清理与影响面分析。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 生成工作空间要素交叉引用表 or similar operations.
description_en: 扫描工作空间，建立数据集与要素之间的交叉引用（被哪些图层/关系引用）清单，用于迁移、清理与影响面分析。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 生成工作空间要素交叉引用表 or similar operations.
description_zh: 扫描工作空间，建立数据集与要素之间的交叉引用（被哪些图层/关系引用）清单，用于迁移、清理与影响面分析。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「生成工作空间要素交叉引用表」或同类操作时使用。
argument-hint: <输入工作空间或要素数据集> <输出文件夹> <输出文件名> <完成后是否打开输出> <数据源类型> <要素类型> <目标结构（输出字段模板）>
argument-hint-en: <输入工作空间或要素数据集> <输出文件夹> <输出文件名> <完成后是否打开输出> <数据源类型> <要素类型> <目标结构（输出字段模板）>
argument-hint-zh: <输入工作空间或要素数据集> <输出文件夹> <输出文件名> <完成后是否打开输出> <数据源类型> <要素类型> <目标结构（输出字段模板）>
user-invocable: true
---

# 生成工作空间要素交叉引用表

## 功能
扫描工作空间，建立数据集与要素之间的交叉引用（被哪些图层/关系引用）清单，用于迁移、清理与影响面分析。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入工作空间或要素数据集
- 输出文件夹
- 输出文件名
- 完成后是否打开输出
- 数据源类型
- 要素类型
- 目标结构（输出字段模板）
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入工作空间或要素数据集（原参数名：Workspace or Feature Dataset）
2. 输出文件夹（原参数名：Output Folder）
3. 输出文件名（原参数名：Output File Name）
4. 完成后是否打开输出（原参数名：Open Output on Complete）
5. 数据源类型（原参数名：Data Source Types）
6. 要素类型（原参数名：Feature Type）
7. 目标结构（输出字段模板）（原参数名：Target Schema）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按上表顺序传入）。
运行环境：ArcGIS Pro

## 执行后复核
- 读回输出的行数/字段值或打开结果文件抽查 3 项；
- 报错时看 traceback 定位到具体参数。

## 详细说明
本技能抽取自社区开源工具箱的单个工具，逻辑与参数保持原实现，仅把参数入口改为命令行传入。

## 参数与调用
```bat
python scripts\run.py <输入工作空间或要素数据集> <输出文件夹> <输出文件名> <完成后是否打开输出> <数据源类型> <要素类型> <目标结构（输出字段模板）>
```
参数说明：

1. 输入工作空间或要素数据集（原参数名：Workspace or Feature Dataset）
2. 输出文件夹（原参数名：Output Folder）
3. 输出文件名（原参数名：Output File Name）
4. 完成后是否打开输出（原参数名：Open Output on Complete）
5. 数据源类型（原参数名：Data Source Types）
6. 要素类型（原参数名：Feature Type）
7. 目标结构（输出字段模板）（原参数名：Target Schema）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
