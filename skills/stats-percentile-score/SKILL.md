---
name: stats-percentile-score
name_en: 字段百分位评分
name_zh: 字段百分位评分
description: 按指定字段的全域百分位给每个要素打分（0~100 或 0~1），用于等级划分、综合评级打分。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 字段百分位评分 or similar operations.
description_en: 按指定字段的全域百分位给每个要素打分（0~100 或 0~1），用于等级划分、综合评级打分。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 字段百分位评分 or similar operations.
description_zh: 按指定字段的全域百分位给每个要素打分（0~100 或 0~1），用于等级划分、综合评级打分。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「字段百分位评分」或同类操作时使用。
argument-hint: <输入要素类> <参与计算的字段（分号分隔）> <分组字段（可选）> <是否反向排名> <评分/排名方式> <NullValueFill> <NumberRank>
argument-hint-en: <输入要素类> <参与计算的字段（分号分隔）> <分组字段（可选）> <是否反向排名> <评分/排名方式> <NullValueFill> <NumberRank>
argument-hint-zh: <输入要素类> <参与计算的字段（分号分隔）> <分组字段（可选）> <是否反向排名> <评分/排名方式> <NullValueFill> <NumberRank>
user-invocable: true
---

# 字段百分位评分

## 功能
按指定字段的全域百分位给每个要素打分（0~100 或 0~1），用于等级划分、综合评级打分。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入要素类
- 参与计算的字段（分号分隔）
- 分组字段（可选）
- 是否反向排名
- 评分/排名方式
- NullValueFill
- NumberRank
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入要素类（原参数名：FeatureClass）
2. 参与计算的字段（分号分隔）（原参数名：InputFields）
3. 分组字段（可选）（原参数名：RankingGroupField）
4. 是否反向排名（原参数名：InvertRank）
5. 评分/排名方式（原参数名：RankMethod）
6. NullValueFill（原参数名：NullValueFill）
7. NumberRank（原参数名：NumberRank）

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
python scripts\run.py <输入要素类> <参与计算的字段（分号分隔）> <分组字段（可选）> <是否反向排名> <评分/排名方式> <NullValueFill> <NumberRank>
```
参数说明：

1. 输入要素类（原参数名：FeatureClass）
2. 参与计算的字段（分号分隔）（原参数名：InputFields）
3. 分组字段（可选）（原参数名：RankingGroupField）
4. 是否反向排名（原参数名：InvertRank）
5. 评分/排名方式（原参数名：RankMethod）
6. NullValueFill（原参数名：NullValueFill）
7. NumberRank（原参数名：NumberRank）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
