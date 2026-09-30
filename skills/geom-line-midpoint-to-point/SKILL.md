---
name: geom-line-midpoint-to-point
name_en: 线中点转点
name_zh: 线中点转点
description: 取每条线的中点生成点要素，常用于标注定位点、抽样点。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 线中点转点 or similar operations.
description_en: 取每条线的中点生成点要素，常用于标注定位点、抽样点。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 线中点转点 or similar operations.
description_zh: 取每条线的中点生成点要素，常用于标注定位点、抽样点。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「线中点转点」或同类操作时使用。
argument-hint: <输入线要素类> <输出点要素类>
argument-hint-en: <输入线要素类> <输出点要素类>
argument-hint-zh: <输入线要素类> <输出点要素类>
user-invocable: true
---

# 线中点转点

## 功能
取每条线的中点生成点要素，常用于标注定位点、抽样点。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入线要素类
- 输出点要素类
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入线要素类（原参数名：in_line_fc）
2. 输出点要素类（原参数名：out_pt_fc）

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
python scripts\run.py <输入线要素类> <输出点要素类>
```
参数说明：

1. 输入线要素类（原参数名：in_line_fc）
2. 输出点要素类（原参数名：out_pt_fc）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
