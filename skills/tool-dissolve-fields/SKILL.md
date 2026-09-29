---
name: tool-dissolve-fields
name_en: 按字段融合并拼接属性
name_zh: 按字段融合并拼接属性
description: 按指定字段融合要素，同时把关联表的字段值拼接（concatenate）写入结果，解决标准 Dissolve 只能保留统计值、丢掉文本清单的问题。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按字段融合并拼接属性 or similar operations.
description_en: 按指定字段融合要素，同时把关联表的字段值拼接（concatenate）写入结果，解决标准 Dissolve 只能保留统计值、丢掉文本清单的问题。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按字段融合并拼接属性 or similar operations.
description_zh: 按指定字段融合要素，同时把关联表的字段值拼接（concatenate）写入结果，解决标准 Dissolve 只能保留统计值、丢掉文本清单的问题。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「按字段融合并拼接属性」或同类操作时使用。
argument-hint: <输入数据集> <输入数据集的分组字段> <关联表> <关联表的字段>
argument-hint-en: <输入数据集> <输入数据集的分组字段> <关联表> <关联表的字段>
argument-hint-zh: <输入数据集> <输入数据集的分组字段> <关联表> <关联表的字段>
user-invocable: true
---

# 按字段融合并拼接属性

## 功能
按指定字段融合要素，同时把关联表的字段值拼接（concatenate）写入结果，解决标准 Dissolve 只能保留统计值、丢掉文本清单的问题。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入数据集
- 输入数据集的分组字段
- 关联表
- 关联表的字段
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入数据集（原参数名：input_dataset）
2. 输入数据集的分组字段（原参数名：input_dataset_field）
3. 关联表（原参数名：input_join）
4. 关联表的字段（原参数名：input_join_field）

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
python scripts\run.py <输入数据集> <输入数据集的分组字段> <关联表> <关联表的字段>
```
参数说明：

1. 输入数据集（原参数名：input_dataset）
2. 输入数据集的分组字段（原参数名：input_dataset_field）
3. 关联表（原参数名：input_join）
4. 关联表的字段（原参数名：input_join_field）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
