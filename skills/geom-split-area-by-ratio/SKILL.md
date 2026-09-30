---
name: geom-split-area-by-ratio
name_en: 按参照面分摊面积
name_zh: 按参照面分摊面积
description: 以另一组面为参照，把源面的指定数值字段按相交面积比例分摊（面积按分），写入输出面，用于指标按占比拆分、跨行政区指标分摊。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按参照面分摊面积 or similar operations.
description_en: 以另一组面为参照，把源面的指定数值字段按相交面积比例分摊（面积按分），写入输出面，用于指标按占比拆分、跨行政区指标分摊。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按参照面分摊面积 or similar operations.
description_zh: 以另一组面为参照，把源面的指定数值字段按相交面积比例分摊（面积按分），写入输出面，用于指标按占比拆分、跨行政区指标分摊。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「按参照面分摊面积」或同类操作时使用。
argument-hint: <输入面要素类> <参照面要素类> <需按面积分摊的数值字段（可多个）> <输出面要素类>
argument-hint-en: <输入面要素类> <参照面要素类> <需按面积分摊的数值字段（可多个）> <输出面要素类>
argument-hint-zh: <输入面要素类> <参照面要素类> <需按面积分摊的数值字段（可多个）> <输出面要素类>
user-invocable: true
---

# 按参照面分摊面积

## 功能
以另一组面为参照，把源面的指定数值字段按相交面积比例分摊（面积按分），写入输出面，用于指标按占比拆分、跨行政区指标分摊。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入面要素类
- 参照面要素类
- 需按面积分摊的数值字段（可多个）
- 输出面要素类
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入面要素类（原参数名：IN_POLY_FC）
2. 参照面要素类（原参数名：REF_POLY_FC）
3. 需按面积分摊的数值字段（可多个）（原参数名：FIELDS）
4. 输出面要素类（原参数名：OUT_POLY_FC）

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
python scripts\run.py <输入面要素类> <参照面要素类> <需按面积分摊的数值字段（可多个）> <输出面要素类>
```
参数说明：

1. 输入面要素类（原参数名：IN_POLY_FC）
2. 参照面要素类（原参数名：REF_POLY_FC）
3. 需按面积分摊的数值字段（可多个）（原参数名：FIELDS）
4. 输出面要素类（原参数名：OUT_POLY_FC）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
