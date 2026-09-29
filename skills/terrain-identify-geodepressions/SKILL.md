---
name: terrain-identify-geodepressions
name_en: 测深栅格凹坑识别
name_zh: 测深栅格凹坑识别
description: 半自动识别测深（或高程）栅格上的凹坑/洼地，按深度阈值与最大面积阈值筛选并输出多边形，用于海底麻坑、地表沉陷等地貌编目。需要 Spatial Analyst 许可。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 测深栅格凹坑识别 or similar operations.
description_en: 半自动识别测深（或高程）栅格上的凹坑/洼地，按深度阈值与最大面积阈值筛选并输出多边形，用于海底麻坑、地表沉陷等地貌编目。需要 Spatial Analyst 许可。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 测深栅格凹坑识别 or similar operations.
description_zh: 半自动识别测深（或高程）栅格上的凹坑/洼地，按深度阈值与最大面积阈值筛选并输出多边形，用于海底麻坑、地表沉陷等地貌编目。需要 Spatial Analyst 许可。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「测深栅格凹坑识别」或同类操作时使用。
argument-hint: <输入测深/高程栅格> <深度阈值> <最大面积阈值> <输出凹坑多边形>
argument-hint-en: <输入测深/高程栅格> <深度阈值> <最大面积阈值> <输出凹坑多边形>
argument-hint-zh: <输入测深/高程栅格> <深度阈值> <最大面积阈值> <输出凹坑多边形>
user-invocable: true
---

# 测深栅格凹坑识别

## 功能
半自动识别测深（或高程）栅格上的凹坑/洼地，按深度阈值与最大面积阈值筛选并输出多边形，用于海底麻坑、地表沉陷等地貌编目。需要 Spatial Analyst 许可。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入测深/高程栅格
- 深度阈值
- 最大面积阈值
- 输出凹坑多边形
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入测深/高程栅格（原参数名：raster_layer）
2. 深度阈值（原参数名：z_limit）
3. 最大面积阈值（原参数名：max_area）
4. 输出凹坑多边形（原参数名：out_polygons）

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
python scripts\run.py <输入测深/高程栅格> <深度阈值> <最大面积阈值> <输出凹坑多边形>
```
参数说明：

1. 输入测深/高程栅格（原参数名：raster_layer）
2. 深度阈值（原参数名：z_limit）
3. 最大面积阈值（原参数名：max_area）
4. 输出凹坑多边形（原参数名：out_polygons）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
