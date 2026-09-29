---
name: geom-circle-from-three-points
name_en: 三点定圆
name_zh: 三点定圆
description: 由三个点（或点要素）求解外接圆，输出圆心与圆面，用于测量放样、圆曲线拟合等场景。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 三点定圆 or similar operations.
description_en: 由三个点（或点要素）求解外接圆，输出圆心与圆面，用于测量放样、圆曲线拟合等场景。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 三点定圆 or similar operations.
description_zh: 由三个点（或点要素）求解外接圆，输出圆心与圆面，用于测量放样、圆曲线拟合等场景。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「三点定圆」或同类操作时使用。
argument-hint: <输入要素类（已加载图层可直接写图层名）> <输出工作空间（GDB）> <输出的圆要素名称> <输出的圆心点要素名称>
argument-hint-en: <输入要素类（已加载图层可直接写图层名）> <输出工作空间（GDB）> <输出的圆要素名称> <输出的圆心点要素名称>
argument-hint-zh: <输入要素类（已加载图层可直接写图层名）> <输出工作空间（GDB）> <输出的圆要素名称> <输出的圆心点要素名称>
user-invocable: true
---

# 三点定圆

## 功能
由三个点（或点要素）求解外接圆，输出圆心与圆面，用于测量放样、圆曲线拟合等场景。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入要素类（已加载图层可直接写图层名）
- 输出工作空间（GDB）
- 输出的圆要素名称
- 输出的圆心点要素名称
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入要素类（已加载图层可直接写图层名）（原参数名：fc）
2. 输出工作空间（GDB）（原参数名：out_fc_gdb）
3. 输出的圆要素名称（原参数名：out_fc_circle_name）
4. 输出的圆心点要素名称（原参数名：out_fc_circle_centroid_name）

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
python scripts\run.py <输入要素类（已加载图层可直接写图层名）> <输出工作空间（GDB）> <输出的圆要素名称> <输出的圆心点要素名称>
```
参数说明：

1. 输入要素类（已加载图层可直接写图层名）（原参数名：fc）
2. 输出工作空间（GDB）（原参数名：out_fc_gdb）
3. 输出的圆要素名称（原参数名：out_fc_circle_name）
4. 输出的圆心点要素名称（原参数名：out_fc_circle_centroid_name）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
