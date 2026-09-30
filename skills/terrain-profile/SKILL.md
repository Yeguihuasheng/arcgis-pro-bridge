---
name: terrain-profile
name_en: DEM 剖面提取
name_zh: DEM 剖面提取
description: 沿指定线在 DEM 上采样高程并输出剖面表与剖面图，用于地形起伏分析、纵横断面校核。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for DEM 剖面提取 or similar operations.
description_en: 沿指定线在 DEM 上采样高程并输出剖面表与剖面图，用于地形起伏分析、纵横断面校核。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for DEM 剖面提取 or similar operations.
description_zh: 沿指定线在 DEM 上采样高程并输出剖面表与剖面图，用于地形起伏分析、纵横断面校核。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「DEM 剖面提取」或同类操作时使用。
argument-hint: <输入 DEM 栅格> <剖面线要素> <输出剖面表> <输出剖面图>
argument-hint-en: <输入 DEM 栅格> <剖面线要素> <输出剖面表> <输出剖面图>
argument-hint-zh: <输入 DEM 栅格> <剖面线要素> <输出剖面表> <输出剖面图>
user-invocable: true
---

# DEM 剖面提取

## 功能
沿指定线在 DEM 上采样高程并输出剖面表与剖面图，用于地形起伏分析、纵横断面校核。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入 DEM 栅格
- 剖面线要素
- 输出剖面表
- 输出剖面图
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入 DEM 栅格（原参数名：inputdem）
2. 剖面线要素（原参数名：inputlinea）
3. 输出剖面表（原参数名：salidatabla）
4. 输出剖面图（原参数名：salidagraf）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按上表顺序传入）。
运行环境：ArcGIS Pro

## 执行后复核
- 读回输出的行数/字段值或打开结果文件抽查 3 项；
- 报错时看 traceback 定位到具体参数。

## 详细说明
本技能抽取自社区开源工具箱的单个工具，逻辑与参数保持原实现，仅把参数入口改为命令行传入。需要 3D Analyst 扩展许可（arcpy.CheckExtension('3D')），许可不可用时脚本会静默跳过、不产出错果，执行后务必复核输出表是否存在。

## 参数与调用
```bat
python scripts\run.py <输入 DEM 栅格> <剖面线要素> <输出剖面表> <输出剖面图>
```
参数说明：

1. 输入 DEM 栅格（原参数名：inputdem）
2. 剖面线要素（原参数名：inputlinea）
3. 输出剖面表（原参数名：salidatabla）
4. 输出剖面图（原参数名：salidagraf）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
