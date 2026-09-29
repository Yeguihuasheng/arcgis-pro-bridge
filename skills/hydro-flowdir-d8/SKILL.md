---
name: hydro-flowdir-d8
name_en: D8 流向与汇流累积计算
name_zh: D8 流向与汇流累积计算
description: 由水文修正 DEM 计算 D8 流向栅格与汇流累积（汇水面积）栅格；ESRI 分水岭工具要求 D8 流向，因此本技能通常作为「按点划定流域」的前置步骤。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for D8 流向与汇流累积计算 or similar operations.
description_en: 由水文修正 DEM 计算 D8 流向栅格与汇流累积（汇水面积）栅格；ESRI 分水岭工具要求 D8 流向，因此本技能通常作为「按点划定流域」的前置步骤。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for D8 流向与汇流累积计算 or similar operations.
description_zh: 由水文修正 DEM 计算 D8 流向栅格与汇流累积（汇水面积）栅格；ESRI 分水岭工具要求 D8 流向，因此本技能通常作为「按点划定流域」的前置步骤。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「D8 流向与汇流累积计算」或同类操作时使用。
argument-hint: <输出工作空间（GDB 或文件夹）> <水文修正 DEM> <并行进程数>
argument-hint-en: <输出工作空间（GDB 或文件夹）> <水文修正 DEM> <并行进程数>
argument-hint-zh: <输出工作空间（GDB 或文件夹）> <水文修正 DEM> <并行进程数>
user-invocable: true
---

# D8 流向与汇流累积计算

## 功能
由水文修正 DEM 计算 D8 流向栅格与汇流累积（汇水面积）栅格；ESRI 分水岭工具要求 D8 流向，因此本技能通常作为「按点划定流域」的前置步骤。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输出工作空间（GDB 或文件夹）
- 水文修正 DEM
- 并行进程数
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输出工作空间（GDB 或文件夹）（原参数名：output_workspace）
2. 水文修正 DEM（原参数名：dem_hydro）
3. 并行进程数（原参数名：processes）

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
python scripts\run.py <输出工作空间（GDB 或文件夹）> <水文修正 DEM> <并行进程数>
```
参数说明：

1. 输出工作空间（GDB 或文件夹）（原参数名：output_workspace）
2. 水文修正 DEM（原参数名：dem_hydro）
3. 并行进程数（原参数名：processes）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
