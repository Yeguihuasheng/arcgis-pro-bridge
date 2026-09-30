---
name: geom-find-centroids
name_en: 查找并生成质心点
name_zh: 查找并生成质心点
description: 按分组条件为面要素求质心并生成点要素，可控制是否只保留落在面内的点，用于标注点与抽样点批量生成。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 查找并生成质心点 or similar operations.
description_en: 按分组条件为面要素求质心并生成点要素，可控制是否只保留落在面内的点，用于标注点与抽样点批量生成。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 查找并生成质心点 or similar operations.
description_zh: 按分组条件为面要素求质心并生成点要素，可控制是否只保留落在面内的点，用于标注点与抽样点批量生成。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「查找并生成质心点」或同类操作时使用。
argument-hint: <输入面要素类> <分组字段> <忽略空值> <是否投影到 WGS 1984> <输出点要素类>
argument-hint-en: <输入面要素类> <分组字段> <忽略空值> <是否投影到 WGS 1984> <输出点要素类>
argument-hint-zh: <输入面要素类> <分组字段> <忽略空值> <是否投影到 WGS 1984> <输出点要素类>
user-invocable: true
---

# 查找并生成质心点

## 功能
按分组条件为面要素求质心并生成点要素，可控制是否只保留落在面内的点，用于标注点与抽样点批量生成。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入面要素类
- 分组字段
- 忽略空值
- 是否投影到 WGS 1984
- 输出点要素类
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入面要素类（原参数名：Polygon Feature Class）
2. 分组字段（原参数名：Group Field）
3. 忽略空值（原参数名：Ignore Null Values）
4. 是否投影到 WGS 1984（原参数名：Project to WGS 1984）
5. 输出点要素类（原参数名：Output Point Feature Class）

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
python scripts\run.py <输入面要素类> <分组字段> <忽略空值> <是否投影到 WGS 1984> <输出点要素类>
```
参数说明：

1. 输入面要素类（原参数名：Polygon Feature Class）
2. 分组字段（原参数名：Group Field）
3. 忽略空值（原参数名：Ignore Null Values）
4. 是否投影到 WGS 1984（原参数名：Project to WGS 1984）
5. 输出点要素类（原参数名：Output Point Feature Class）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
