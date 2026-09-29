---
name: hydro-watershed-by-point
name_en: 按点划定上游流域
name_zh: 按点划定上游流域
description: 为输入的每个点计算上游排水流域（分水岭），并可选按地表覆盖栅格统计各流域内的地类面积，写进以地类编码命名的字段。需要 D8 流向与汇流累积栅格。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按点划定上游流域 or similar operations.
description_en: 为输入的每个点计算上游排水流域（分水岭），并可选按地表覆盖栅格统计各流域内的地类面积，写进以地类编码命名的字段。需要 D8 流向与汇流累积栅格。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按点划定上游流域 or similar operations.
description_zh: 为输入的每个点计算上游排水流域（分水岭），并可选按地表覆盖栅格统计各流域内的地类面积，写进以地类编码命名的字段。需要 D8 流向与汇流累积栅格。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「按点划定上游流域」或同类操作时使用。
argument-hint: <输出要素数据集> <输入点要素类> <点要素的 ID 字段> <汇流累积（D8）栅格> <D8 流向栅格> <捕捉距离> <地表覆盖栅格（可选）>
argument-hint-en: <输出要素数据集> <输入点要素类> <点要素的 ID 字段> <汇流累积（D8）栅格> <D8 流向栅格> <捕捉距离> <地表覆盖栅格（可选）>
argument-hint-zh: <输出要素数据集> <输入点要素类> <点要素的 ID 字段> <汇流累积（D8）栅格> <D8 流向栅格> <捕捉距离> <地表覆盖栅格（可选）>
user-invocable: true
---

# 按点划定上游流域

## 功能
为输入的每个点计算上游排水流域（分水岭），并可选按地表覆盖栅格统计各流域内的地类面积，写进以地类编码命名的字段。需要 D8 流向与汇流累积栅格。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输出要素数据集
- 输入点要素类
- 点要素的 ID 字段
- 汇流累积（D8）栅格
- D8 流向栅格
- 捕捉距离
- 地表覆盖栅格（可选）
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输出要素数据集（原参数名：feature_dataset）
2. 输入点要素类（原参数名：points）
3. 点要素的 ID 字段（原参数名：point_ID_field）
4. 汇流累积（D8）栅格（原参数名：flow_accumulation）
5. D8 流向栅格（原参数名：flow_direction_d8）
6. 捕捉距离（原参数名：snap_distance）
7. 地表覆盖栅格（可选）（原参数名：landcover）

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
python scripts\run.py <输出要素数据集> <输入点要素类> <点要素的 ID 字段> <汇流累积（D8）栅格> <D8 流向栅格> <捕捉距离> <地表覆盖栅格（可选）>
```
参数说明：

1. 输出要素数据集（原参数名：feature_dataset）
2. 输入点要素类（原参数名：points）
3. 点要素的 ID 字段（原参数名：point_ID_field）
4. 汇流累积（D8）栅格（原参数名：flow_accumulation）
5. D8 流向栅格（原参数名：flow_direction_d8）
6. 捕捉距离（原参数名：snap_distance）
7. 地表覆盖栅格（可选）（原参数名：landcover）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
