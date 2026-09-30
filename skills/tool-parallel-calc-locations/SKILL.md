---
name: tool-parallel-calc-locations
name_en: 并行批量计算网络位置
name_zh: 并行批量计算网络位置
description: 并行地为大量停靠点计算网络分析位置（网络位置字段），显著加速大规模路径/OD 分析的准备步骤；需要 Network Analyst 许可。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 并行批量计算网络位置 or similar operations.
description_en: 并行地为大量停靠点计算网络分析位置（网络位置字段），显著加速大规模路径/OD 分析的准备步骤；需要 Network Analyst 许可。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 并行批量计算网络位置 or similar operations.
description_zh: 并行地为大量停靠点计算网络分析位置（网络位置字段），显著加速大规模路径/OD 分析的准备步骤；需要 Network Analyst 许可。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「并行批量计算网络位置」或同类操作时使用。
argument-hint: <输入要素> <输出要素> <网络数据集> <每块最大要素数> <最大并行进程数> <出行模式> <搜索容差> <搜索条件> <搜索条件（按字段筛选）>
argument-hint-en: <输入要素> <输出要素> <网络数据集> <每块最大要素数> <最大并行进程数> <出行模式> <搜索容差> <搜索条件> <搜索条件（按字段筛选）>
argument-hint-zh: <输入要素> <输出要素> <网络数据集> <每块最大要素数> <最大并行进程数> <出行模式> <搜索容差> <搜索条件> <搜索条件（按字段筛选）>
user-invocable: true
---

# 并行批量计算网络位置

## 功能
并行地为大量停靠点计算网络分析位置（网络位置字段），显著加速大规模路径/OD 分析的准备步骤；需要 Network Analyst 许可。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入要素
- 输出要素
- 网络数据集
- 每块最大要素数
- 最大并行进程数
- 出行模式
- 搜索容差
- 搜索条件
- 搜索条件（按字段筛选）
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入要素（原参数名：Input Features）
2. 输出要素（原参数名：Output Features）
3. 网络数据集（原参数名：Network Dataset）
4. 每块最大要素数（原参数名：Maximum Features per Chunk）
5. 最大并行进程数（原参数名：Maximum Number of Parallel Processes）
6. 出行模式（原参数名：Travel Mode）
7. 搜索容差（原参数名：Search Tolerance）
8. 搜索条件（原参数名：Search Criteria）
9. 搜索条件（按字段筛选）（原参数名：Search Query）

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
python scripts\run.py <输入要素> <输出要素> <网络数据集> <每块最大要素数> <最大并行进程数> <出行模式> <搜索容差> <搜索条件> <搜索条件（按字段筛选）>
```
参数说明：

1. 输入要素（原参数名：Input Features）
2. 输出要素（原参数名：Output Features）
3. 网络数据集（原参数名：Network Dataset）
4. 每块最大要素数（原参数名：Maximum Features per Chunk）
5. 最大并行进程数（原参数名：Maximum Number of Parallel Processes）
6. 出行模式（原参数名：Travel Mode）
7. 搜索容差（原参数名：Search Tolerance）
8. 搜索条件（原参数名：Search Criteria）
9. 搜索条件（按字段筛选）（原参数名：Search Query）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
