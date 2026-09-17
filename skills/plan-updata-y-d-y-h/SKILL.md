---
name: plan-updata-y-d-y-h
name_en: 赋值用地用海编码和名称
name_zh: 赋值用地用海编码和名称
description: 赋值用地用海编码和名称 (规划应用). Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 赋值用地用海编码和名称 or similar operations.
description_en: 赋值用地用海编码和名称 (规划应用). Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 赋值用地用海编码和名称 or similar operations.
description_zh: 业务技能：赋值用地用海编码和名称（规划应用）。经 YghsBridge MCP 在 ArcGIS Pro 内执行。用户提到「赋值用地用海编码和名称」或同类操作时使用。
argument-hint: Target layer/fields and output path, e.g. layer=图层X field=DLBM out=out.gdb\fc
argument-hint-en: Target layer/fields and output path
argument-hint-zh: 给出目标图层/字段与输出位置，如：图层=地块，字段=DLBM，输出=默认GDB\结果
user-invocable: true
---

# 赋值用地用海编码和名称

## 功能
赋值用地用海编码和名称。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入图层/表（名称或路径）
- 目标字段（若涉及属性写入）
- 关键算法参数（单位/分级/阈值）
- 输出位置（GDB 要素类 / xlsx 路径）
- 坐标系要求：沿用当前工程

**原窗体参数项**（提取自界面定义，作问询参照）：选图层： ／ 选用地： ／ 用地版本： ／ 编码字段： ／ 名称字段：

## 执行路径
✅ 首选本插件：**用地工具箱▶用地代码工具（本插件）** —— 打开对应按钮窗体，按下方参数填写后执行。
若插件未安装：先部署 YghsBridge 插件包（本仓库 bridge-addin 构建产物 esriAddinX，双击安装并重启 Pro）。
备选：按下表参数用桥 arcpy 脚本等效实现。

## 执行后复核
- 读回输出图层行数/字段值或打开 xlsx 抽查 3 项与预期一致；
- 异常时读取 `%LOCALAPPDATA%\LzxRoadToolbox\Logs\RoadToolsDiagnostics.log`（插件路线）或桥返回的 traceback 定位。

## 详细说明（原帮助文档）

赋值用地用海编码和名称 【赋值用地用海编码和名称】
所属分组：规划应用 ｜ 执行方式：🟢 插件直执行
一、简介
控规编制相关：线转道路、交叉口、五线、指标与用地处理。。本条属于「规划应用」组。
二、参数介绍
标准问询参数（该功能为命令式入口，参数以问询确认）说明
 | 目标图层/要素类 | 工作输入，支持地图图层名或 GDB/SHP/要素类路径
 | 关键字段 | 参与计算的字段（代码/面积/名称等），可留自动探测
 | 算法参数 | 单位（平方米/公顷/亩）、小数位、分级阈值等
 | 输出位置 | 默认 GDB 的新要素类，或 xlsx 文件路径
 | 坐标系 | 涉及面积长度时需投影坐标系（米）
三、执行方式
原工具箱插件（打开 Pro 顶部对应选项卡按钮窗体，参数按下表填写后执行）
四、提示词指引
▍直接唤起
「执行功能：赋值用地用海编码和名称，目标图层：问我要」
▍问询式对话（默认流程）
你：赋值用地用海编码和名称
助手：逐项确认——输入图层？关键字段？单位与小数位？输出位置？坐标系——全部确认后才执行。
助手：执行→读回结果→汇报差异并给出成果路径。
五、结果与复核
输出为新要素类或 xlsx（以参数确认结果为准）；复核三件事：行数/地物数、3 个抽样字段值、成果文件非空。
六、注意事项
①涉及面积、长度、距离的功能需投影坐标系；②写入被地图引用的数据请经插件或桥（Pro 主线程）执行；③结果表版式沿用行业通行表样。

## 原始实现要点（完整源码已附在本技能 source/ 目录，等效复现以此为准）

**源码**：完整随附于本技能目录——`source/UpdataYDYH.xaml`、`source/UpdataYDYH.xaml.cs`

**算法**：交互式赋值——用户在窗体里选定「用地用海分类」（级联选择），对**当前选中的要素**
批量写入编码与名称两字段：bm = 编码（名称去掉汉字后的代码）、mc = 名称。
桥等效实现：AI 先问「要赋的用地用海分类」与目标要素选择条件（或 OID 列表），
再 SearchCursor/UpdateCursor 写两字段。注意原版只处理**选中要素**，桥实现用 SQL 限定范围。

