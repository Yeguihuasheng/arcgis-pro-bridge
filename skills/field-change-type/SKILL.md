---
name: field-change-type
name_en: 修改字段类型
name_zh: 修改字段类型
description: 在不重建表的前提下把指定字段改写成目标类型（如文本转长整/双精度），适用于标准要求的类型整改。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 修改字段类型 or similar operations.
description_en: 在不重建表的前提下把指定字段改写成目标类型（如文本转长整/双精度），适用于标准要求的类型整改。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 修改字段类型 or similar operations.
description_zh: 在不重建表的前提下把指定字段改写成目标类型（如文本转长整/双精度），适用于标准要求的类型整改。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「修改字段类型」或同类操作时使用。
argument-hint: <输入表> <字段（可多选）> <新字段类型（TEXT / LONG / DOUBLE 等）>
argument-hint-en: <输入表> <字段（可多选）> <新字段类型（TEXT / LONG / DOUBLE 等）>
argument-hint-zh: <输入表> <字段（可多选）> <新字段类型（TEXT / LONG / DOUBLE 等）>
user-invocable: true
---

# 修改字段类型

## 功能
在不重建表的前提下把指定字段改写成目标类型（如文本转长整/双精度），适用于标准要求的类型整改。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入表
- 字段（可多选）
- 新字段类型（TEXT / LONG / DOUBLE 等）
- 输出位置（GDB 要素类 / 表 / csv 路径）
- 坐标系要求：沿用当前工程

**原工具参数项**（提取自开源实现，作问询参照）：
1. 输入表（原工具参数名：Input Table）
2. 字段（可多选）（原工具参数名：Fields）
3. 新字段类型（TEXT / LONG / DOUBLE 等）（原工具参数名：New Field Type）

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
python scripts\run.py <输入表> <字段（可多选）> <新字段类型（TEXT / LONG / DOUBLE 等）>
```
参数说明：
1. 输入表（原工具参数名：Input Table）
2. 字段（可多选）（原工具参数名：Fields）
3. 新字段类型（TEXT / LONG / DOUBLE 等）（原工具参数名：New Field Type）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
