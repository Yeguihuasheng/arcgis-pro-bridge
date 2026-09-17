---
name: plan-remove0-d-m
name_en: 移除用地代码后的0
name_zh: 移除用地代码后的0
description: 移除用地代码后的0 (规划应用). Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 移除用地代码后的0 or similar operations.
description_en: 移除用地代码后的0 (规划应用). Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 移除用地代码后的0 or similar operations.
description_zh: 业务技能：移除用地代码后的0（规划应用）。经 YghsBridge MCP 在 ArcGIS Pro 内执行。用户提到「移除用地代码后的0」或同类操作时使用。
argument-hint: Target layer/fields and output path, e.g. layer=图层X field=DLBM out=out.gdb\fc
argument-hint-en: Target layer/fields and output path
argument-hint-zh: 给出目标图层/字段与输出位置，如：图层=地块，字段=DLBM，输出=默认GDB\结果
user-invocable: true
---

# 移除用地代码后的0

## 功能
移除用地代码后的0。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入图层/表（名称或路径）
- 目标字段（若涉及属性写入）
- 关键算法参数（单位/分级/阈值）
- 输出位置（GDB 要素类 / xlsx 路径）
- 坐标系要求：沿用当前工程

**原窗体参数项**（提取自界面定义，作问询参照）：选择图层或表： ／ 选择用地代码字段：

## 执行路径
✅ 首选本插件：**用地工具箱▶用地代码工具（本插件）** —— 打开对应按钮窗体，按下方参数填写后执行。
若插件未安装：先部署 YghsBridge 插件包（本仓库 bridge-addin 构建产物 esriAddinX，双击安装并重启 Pro）。
备选：按下表参数用桥 arcpy 脚本等效实现。

## 执行后复核
- 读回输出图层行数/字段值或打开 xlsx 抽查 3 项与预期一致；
- 异常时读取 `%LOCALAPPDATA%\LzxRoadToolbox\Logs\RoadToolsDiagnostics.log`（插件路线）或桥返回的 traceback 定位。

## 详细说明（原帮助文档）

移除用地代码后的0 【移除用地代码后的0】
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
「执行功能：移除用地代码后的0，目标图层：问我要」
▍问询式对话（默认流程）
你：移除用地代码后的0
助手：逐项确认——输入图层？关键字段？单位与小数位？输出位置？坐标系——全部确认后才执行。
助手：执行→读回结果→汇报差异并给出成果路径。
五、结果与复核
输出为新要素类或 xlsx（以参数确认结果为准）；复核三件事：行数/地物数、3 个抽样字段值、成果文件非空。
六、注意事项
①涉及面积、长度、距离的功能需投影坐标系；②写入被地图引用的数据请经插件或桥（Pro 主线程）执行；③结果表版式沿用行业通行表样。

## 原始实现要点（完整源码已附在本技能 source/ 目录，等效复现以此为准）

**源码**：完整随附于本技能目录——`source/Remove0DM.xaml`、`source/Remove0DM.xaml.cs`

**算法（原版代码块，逐字保留）**：对指定文本字段做 CalculateField，代码块：

```python
def ss(a):
    if a[2:] == '0'*(len(a)-2):
        return a[:2]
    elif a[4:] == '0'*(len(a)-4):
        return a[:4]
    else:
        return a
```

语义：用地代码只保留 **2 位大类** 或 **4 位中类** 主干，砍掉其后的补位 0。
注意：不是简单 rstrip('0')——长度为 3 的 "100" 会得到 "10"（rstrip 会错成 "1"）。
GP 调用：`management.CalculateField(fc, field, "ss(!field!)", codeblock)`。

