---
name: tool-merge-by-crossref
name_en: 按交叉引用合并要素
name_zh: 按交叉引用合并要素
description: 依据交叉引用表把一批要素按相同的引用关系合并输出，用于把分散存放但同属一类的数据整合到一张表。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按交叉引用合并要素 or similar operations.
description_en: 依据交叉引用表把一批要素按相同的引用关系合并输出，用于把分散存放但同属一类的数据整合到一张表。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按交叉引用合并要素 or similar operations.
description_zh: 依据交叉引用表把一批要素按相同的引用关系合并输出，用于把分散存放但同属一类的数据整合到一张表。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「按交叉引用合并要素」或同类操作时使用。
argument-hint: <输入交叉引用表> <输出坐标系> <输出要素类> <目标结构（输出字段模板）>
argument-hint-en: <输入交叉引用表> <输出坐标系> <输出要素类> <目标结构（输出字段模板）>
argument-hint-zh: <输入交叉引用表> <输出坐标系> <输出要素类> <目标结构（输出字段模板）>
user-invocable: true
---

# 按交叉引用合并要素

## 功能
依据交叉引用表把一批要素按相同的引用关系合并输出，用于把分散存放但同属一类的数据整合到一张表。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入交叉引用表
- 输出坐标系
- 输出要素类
- 目标结构（输出字段模板）
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入交叉引用表（原参数名：Input Cross Reference File）
2. 输出坐标系（原参数名：Output Spatial Reference）
3. 输出要素类（原参数名：Output Featureclass）
4. 目标结构（输出字段模板）（原参数名：Target Schema）

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
python scripts\run.py <输入交叉引用表> <输出坐标系> <输出要素类> <目标结构（输出字段模板）>
```
参数说明：

1. 输入交叉引用表（原参数名：Input Cross Reference File）
2. 输出坐标系（原参数名：Output Spatial Reference）
3. 输出要素类（原参数名：Output Featureclass）
4. 目标结构（输出字段模板）（原参数名：Target Schema）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
