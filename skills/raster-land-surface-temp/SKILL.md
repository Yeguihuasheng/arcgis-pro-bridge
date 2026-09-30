---
name: raster-land-surface-temp
name_en: 地表温度反演（Landsat）
name_zh: 地表温度反演（Landsat）
description: 从 Landsat 影像产品文件夹反演地表温度（LST），输出温度栅格，用于热环境分析、城市热岛评估。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 地表温度反演（Landsat） or similar operations.
description_en: 从 Landsat 影像产品文件夹反演地表温度（LST），输出温度栅格，用于热环境分析、城市热岛评估。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 地表温度反演（Landsat） or similar operations.
description_zh: 从 Landsat 影像产品文件夹反演地表温度（LST），输出温度栅格，用于热环境分析、城市热岛评估。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「地表温度反演（Landsat）」或同类操作时使用。
argument-hint: <Landsat 产品文件夹> <反演产品类型> <掩膜要素（可选）> <是否采用 B11 波段均值>
argument-hint-en: <Landsat 产品文件夹> <反演产品类型> <掩膜要素（可选）> <是否采用 B11 波段均值>
argument-hint-zh: <Landsat 产品文件夹> <反演产品类型> <掩膜要素（可选）> <是否采用 B11 波段均值>
user-invocable: true
---

# 地表温度反演（Landsat）

## 功能
从 Landsat 影像产品文件夹反演地表温度（LST），输出温度栅格，用于热环境分析、城市热岛评估。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- Landsat 产品文件夹
- 反演产品类型
- 掩膜要素（可选）
- 是否采用 B11 波段均值
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. Landsat 产品文件夹（原参数名：user_folder）
2. 反演产品类型（原参数名：products）
3. 掩膜要素（可选）（原参数名：mask_feature）
4. 是否采用 B11 波段均值（原参数名：average_b11）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按上表顺序传入）。
运行环境：ArcGIS Pro

## 执行后复核
- 读回输出的行数/字段值或打开结果文件抽查 3 项；
- 报错时看 traceback 定位到具体参数。

## 详细说明
依赖 Spatial Analyst 扩展（arcpy.sa）；输入为 Landsat 产品解压后的文件夹，工具自动读取元数据中的辐射定标参数。

## 参数与调用
```bat
python scripts\run.py <Landsat 产品文件夹> <反演产品类型> <掩膜要素（可选）> <是否采用 B11 波段均值>
```
参数说明：

1. Landsat 产品文件夹（原参数名：user_folder）
2. 反演产品类型（原参数名：products）
3. 掩膜要素（可选）（原参数名：mask_feature）
4. 是否采用 B11 波段均值（原参数名：average_b11）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
