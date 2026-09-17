---
name: territory-z-y1
name_en: 国土空间调查辅助·地类统计
name_zh: 国土空间调查辅助·地类统计
description: 工具简介 (国土应用). Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 工具简介 or similar operations.
description_en: 工具简介 (国土应用). Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 工具简介 or similar operations.
description_zh: 业务技能：工具简介（国土应用）。经 YghsBridge MCP 在 ArcGIS Pro 内执行。用户提到「工具简介」或同类操作时使用。
argument-hint: Target layer/fields and output path, e.g. layer=图层X field=DLBM out=out.gdb\fc
argument-hint-en: Target layer/fields and output path
argument-hint-zh: 给出目标图层/字段与输出位置，如：图层=地块，字段=DLBM，输出=默认GDB\结果
user-invocable: true
---

# 工具简介

## 功能
工具简介。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入图层/表（名称或路径）
- 目标字段（若涉及属性写入）
- 关键算法参数（单位/分级/阈值）
- 输出位置（GDB 要素类 / xlsx 路径）
- 坐标系要求：沿用当前工程

## 执行路径
🔌 通过 ArcProBridge 在 Pro 内执行 arcpy/Pro SDK 等效实现（见总指引技能的桥用法）；
本功能为 历史来源工具 自研算法，无直接 GP 对应，按参数逐项落地。

## 执行后复核
- 读回输出图层行数/字段值或打开 xlsx 抽查 3 项与预期一致；
- 异常时读取 `%LOCALAPPDATA%\LzxRoadToolbox\Logs\RoadToolsDiagnostics.log`（插件路线）或桥返回的 traceback 定位。

## 详细说明（原帮助文档）

工具简介 【工具简介】
所属分组：国土应用 ｜ 执行方式：🔵 桥脚本执行
一、简介
国土空间调查与规划：地类统计、三大类、编码转换、双评价辅助。。本条属于「国土应用」组。
二、参数介绍
标准问询参数（该功能为命令式入口，参数以问询确认）说明
 | 目标图层/要素类 | 工作输入，支持地图图层名或 GDB/SHP/要素类路径
 | 关键字段 | 参与计算的字段（代码/面积/名称等），可留自动探测
 | 算法参数 | 单位（平方米/公顷/亩）、小数位、分级阈值等
 | 输出位置 | 默认 GDB 的新要素类，或 xlsx 文件路径
 | 坐标系 | 涉及面积长度时需投影坐标系（米）
三、执行方式
ArcProBridge arcpy 通道执行（Pro 内 Python 等效实现，脚本骨架见「开始使用」章）
四、提示词指引
▍直接唤起
「执行功能：工具简介，目标图层：问我要」
▍问询式对话（默认流程）
你：工具简介
助手：逐项确认——输入图层？关键字段？单位与小数位？输出位置？坐标系——全部确认后才执行。
助手：执行→读回结果→汇报差异并给出成果路径。
五、结果与复核
输出为新要素类或 xlsx（以参数确认结果为准）；复核三件事：行数/地物数、3 个抽样字段值、成果文件非空。
六、注意事项
①涉及面积、长度、距离的功能需投影坐标系；②写入被地图引用的数据请经插件或桥（Pro 主线程）执行；③结果表版式沿用行业通行表样。

## 原始实现要点（完整源码已附在本技能 source/ 目录，等效复现以此为准）

**源码**：无独立源码文件（本技能按下方要点直接实现）

**说明**：本技能为通用辅助功能，无独立源码文件，按下方要点直接等效实现。
等效实现按 SKILL.md 问询清单执行：地类统计（Statistics 按地类字段求面积和）、
三大类归并（编码前 2 位映射农用地/建设用地/未利用地）、编码转换（查三调规程表）、双评价辅助。

