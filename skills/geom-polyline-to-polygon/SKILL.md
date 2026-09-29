---
name: geom-polyline-to-polygon
name_en: 线转面
name_zh: 线转面
description: 把闭合的线要素转换为面要素（支持按分组字段分别成面），用于把采集的封闭边界线转成地块面。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 线转面 or similar operations.
description_en: 把闭合的线要素转换为面要素（支持按分组字段分别成面），用于把采集的封闭边界线转成地块面。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 线转面 or similar operations.
description_zh: 把闭合的线要素转换为面要素（支持按分组字段分别成面），用于把采集的封闭边界线转成地块面。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「线转面」或同类操作时使用。
argument-hint: <输入要素类（已加载图层可直接写图层名）> <输出工作空间（GDB）> <输出要素类名称>
argument-hint-en: <输入要素类（已加载图层可直接写图层名）> <输出工作空间（GDB）> <输出要素类名称>
argument-hint-zh: <输入要素类（已加载图层可直接写图层名）> <输出工作空间（GDB）> <输出要素类名称>
user-invocable: true
---

# 线转面

## 功能
把闭合的线要素转换为面要素（支持按分组字段分别成面），用于把采集的封闭边界线转成地块面。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入要素类（已加载图层可直接写图层名）
- 输出工作空间（GDB）
- 输出要素类名称
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入要素类（已加载图层可直接写图层名）（原参数名：fc）
2. 输出工作空间（GDB）（原参数名：out_fc_gdb）
3. 输出要素类名称（原参数名：out_fc_name）

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
python scripts\run.py <输入要素类（已加载图层可直接写图层名）> <输出工作空间（GDB）> <输出要素类名称>
```
参数说明：

1. 输入要素类（已加载图层可直接写图层名）（原参数名：fc）
2. 输出工作空间（GDB）（原参数名：out_fc_gdb）
3. 输出要素类名称（原参数名：out_fc_name）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
