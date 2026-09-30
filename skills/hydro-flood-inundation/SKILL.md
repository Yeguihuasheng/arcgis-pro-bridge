---
name: hydro-flood-inundation
name_en: 洪水淹没范围分析
name_zh: 洪水淹没范围分析
description: 按给定点位与水位字段在 DEM 上推算洪水淹没范围并输出淹没区，用于洪涝风险评估、淹没示意。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 洪水淹没范围分析 or similar operations.
description_en: 按给定点位与水位字段在 DEM 上推算洪水淹没范围并输出淹没区，用于洪涝风险评估、淹没示意。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 洪水淹没范围分析 or similar operations.
description_zh: 按给定点位与水位字段在 DEM 上推算洪水淹没范围并输出淹没区，用于洪涝风险评估、淹没示意。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「洪水淹没范围分析」或同类操作时使用。
argument-hint: <输入点位表> <裁剪 DEM 的范围要素> <output_folder> <水位字段> <临时工作空间（可选）>
argument-hint-en: <输入点位表> <裁剪 DEM 的范围要素> <output_folder> <水位字段> <临时工作空间（可选）>
argument-hint-zh: <输入点位表> <裁剪 DEM 的范围要素> <output_folder> <水位字段> <临时工作空间（可选）>
user-invocable: true
---

# 洪水淹没范围分析

## 功能
按给定点位与水位字段在 DEM 上推算洪水淹没范围并输出淹没区，用于洪涝风险评估、淹没示意。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入点位表
- 裁剪 DEM 的范围要素
- output_folder
- 水位字段
- 临时工作空间（可选）
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入点位表（原参数名：in_table_main）
2. 裁剪 DEM 的范围要素（原参数名：clip_dem_ft）
3. output_folder（原参数名：output_folder）
4. 水位字段（原参数名：Inundation_Field）
5. 临时工作空间（可选）（原参数名：scratchWorkspace）

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
python scripts\run.py <输入点位表> <裁剪 DEM 的范围要素> <output_folder> <水位字段> <临时工作空间（可选）>
```
参数说明：

1. 输入点位表（原参数名：in_table_main）
2. 裁剪 DEM 的范围要素（原参数名：clip_dem_ft）
3. output_folder（原参数名：output_folder）
4. 水位字段（原参数名：Inundation_Field）
5. 临时工作空间（可选）（原参数名：scratchWorkspace）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
