---
name: hydro-stream-network-points
name_en: 河网转点并统计排水面积
name_zh: 河网转点并统计排水面积
description: 把河网线要素转为节点点，并给每个点挂上排水面积、高程与路由属性，用于按排水面积把河网切分成相对均质的河段。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 河网转点并统计排水面积 or similar operations.
description_en: 把河网线要素转为节点点，并给每个点挂上排水面积、高程与路由属性，用于按排水面积把河网切分成相对均质的河段。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 河网转点并统计排水面积 or similar operations.
description_zh: 把河网线要素转为节点点，并给每个点挂上排水面积、高程与路由属性，用于按排水面积把河网切分成相对均质的河段。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「河网转点并统计排水面积」或同类操作时使用。
argument-hint: <输出要素数据集> <输入河网要素类> <汇流累积栅格> <输入 DEM 栅格>
argument-hint-en: <输出要素数据集> <输入河网要素类> <汇流累积栅格> <输入 DEM 栅格>
argument-hint-zh: <输出要素数据集> <输入河网要素类> <汇流累积栅格> <输入 DEM 栅格>
user-invocable: true
---

# 河网转点并统计排水面积

## 功能
把河网线要素转为节点点，并给每个点挂上排水面积、高程与路由属性，用于按排水面积把河网切分成相对均质的河段。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输出要素数据集
- 输入河网要素类
- 汇流累积栅格
- 输入 DEM 栅格
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输出要素数据集（原参数名：feature_dataset）
2. 输入河网要素类（原参数名：stream_network）
3. 汇流累积栅格（原参数名：flow_accum）
4. 输入 DEM 栅格（原参数名：dem）

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
python scripts\run.py <输出要素数据集> <输入河网要素类> <汇流累积栅格> <输入 DEM 栅格>
```
参数说明：

1. 输出要素数据集（原参数名：feature_dataset）
2. 输入河网要素类（原参数名：stream_network）
3. 汇流累积栅格（原参数名：flow_accum）
4. 输入 DEM 栅格（原参数名：dem）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
