---
name: plan-s-q-s-x-statistics
name_en: 三线占用情况汇总表
name_zh: 三线占用情况汇总表
description: 三线占用情况汇总表 (规划应用). Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 三线占用情况汇总表 or similar operations.
description_en: 三线占用情况汇总表 (规划应用). Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 三线占用情况汇总表 or similar operations.
description_zh: 业务技能：三线占用情况汇总表（规划应用）。经 YghsBridge MCP 在 ArcGIS Pro 内执行。用户提到「三线占用情况汇总表」或同类操作时使用。
argument-hint: Target layer/fields and output path, e.g. layer=图层X field=DLBM out=out.gdb\fc
argument-hint-en: Target layer/fields and output path
argument-hint-zh: 给出目标图层/字段与输出位置，如：图层=地块，字段=DLBM，输出=默认GDB\结果
user-invocable: true
---

# 三线占用情况汇总表

## 功能
三线占用情况汇总表。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入图层/表（名称或路径）
- 目标字段（若涉及属性写入）
- 关键算法参数（单位/分级/阈值）
- 输出位置（GDB 要素类 / xlsx 路径）
- 坐标系要求：沿用当前工程

**原窗体参数项**（提取自界面定义，作问询参照）：选择城镇开发边界： ／ 输出Excel文件路径： ／ 选择分区名称字段： ／ 面积类型： ／ 面积单位： ／ 选择永久基本农田： ／ 选择生态保护红线： ／ 选择分区图层：

## 执行路径
🔌 通过 ArcProBridge 在 Pro 内执行 arcpy/Pro SDK 等效实现（见总指引技能的桥用法）；
本功能为 历史来源工具 自研算法，无直接 GP 对应，按参数逐项落地。

## 执行后复核
- 读回输出图层行数/字段值或打开 xlsx 抽查 3 项与预期一致；
- 异常时读取 `%LOCALAPPDATA%\LzxRoadToolbox\Logs\RoadToolsDiagnostics.log`（插件路线）或桥返回的 traceback 定位。

## 详细说明（原帮助文档）

三线占用情况汇总表 【三线占用情况汇总表】
所属分组：规划应用 ｜ 执行方式：🔵 桥脚本执行
一、简介
聚合同类要素并汇总指标。本条属于「规划应用」组。
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
「执行功能：三线占用情况汇总表，目标图层：问我要」
▍问询式对话（默认流程）
你：三线占用情况汇总表
助手：逐项确认——输入图层？关键字段？单位与小数位？输出位置？坐标系——全部确认后才执行。
助手：执行→读回结果→汇报差异并给出成果路径。
五、结果与复核
输出为新要素类或 xlsx（以参数确认结果为准）；复核三件事：行数/地物数、3 个抽样字段值、成果文件非空。
六、注意事项
①涉及面积、长度、距离的功能需投影坐标系；②写入被地图引用的数据请经插件或桥（Pro 主线程）执行；③结果表版式沿用行业通行表样。

## 原始实现要点（完整源码已附在本技能 source/ 目录，等效复现以此为准）

**源码**：完整随附于本技能目录——`source/SQSXStatistics.xaml`、`source/SQSXStatistics.xaml.cs`

**算法**（三区三线 vs 分区）：对 开发边界/永基农田/生态红线 三个图层逐个：
1. `analysis.Clip(item, zone)` → `analysis.Identity(clip, zone)` → 加 mj_sx；
2. 面积：投影=`!shape.area!`，椭球=`!shape.geodesicarea!`；**永基农田要乘扣减系数**：
   `!shape.area!*(1-!KCXS!)`（KCXS 为基本农田图层的扣减系数字段）；
3. `management.Statistics(out_zone, out_table, "mj_sx SUM", mcField)`（按分区名字段分组）；
4. 写模板【模板】三区三线指标汇总表.xlsx：按分区名复制行，三线分别写 2/3/4 列，加合计行，改单位标注。


**依赖资源**：已复制到本技能 `resources/` 子目录（1 份）。
