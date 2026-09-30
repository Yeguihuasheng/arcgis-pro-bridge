---
name: geom-line-junction-to-point
name_en: 线交点转点
name_zh: 线交点转点
description: 求线要素之间的交点（共有点）并生成点要素，可设置重复点的处理方式，用于生成路网节点、管线交点。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 线交点转点 or similar operations.
description_en: 求线要素之间的交点（共有点）并生成点要素，可设置重复点的处理方式，用于生成路网节点、管线交点。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 线交点转点 or similar operations.
description_zh: 求线要素之间的交点（共有点）并生成点要素，可设置重复点的处理方式，用于生成路网节点、管线交点。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「线交点转点」或同类操作时使用。
argument-hint: <输入线要素类> <输出点要素类> <重复点处理方式>
argument-hint-en: <输入线要素类> <输出点要素类> <重复点处理方式>
argument-hint-zh: <输入线要素类> <输出点要素类> <重复点处理方式>
user-invocable: true
---

# 线交点转点

## 功能
求线要素之间的交点（共有点）并生成点要素，可设置重复点的处理方式，用于生成路网节点、管线交点。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入线要素类
- 输出点要素类
- 重复点处理方式
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入线要素类（原参数名：in_line_fc）
2. 输出点要素类（原参数名：out_pt_fc）
3. 重复点处理方式（原参数名：overlap）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按上表顺序传入）。
运行环境：ArcGIS Pro

## 执行后复核
- 读回输出的行数/字段值或打开结果文件抽查 3 项；
- 报错时看 traceback 定位到具体参数。

## 详细说明
第 3 个参数 overlap 为布尔值：true 表示重合的交点只保留一个；输入只有单条线、没有交点时输出 0 个点属正常。

## 参数与调用
```bat
python scripts\run.py <输入线要素类> <输出点要素类> <重复点处理方式>
```
参数说明：

1. 输入线要素类（原参数名：in_line_fc）
2. 输出点要素类（原参数名：out_pt_fc）
3. 重复点处理方式（原参数名：overlap）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
