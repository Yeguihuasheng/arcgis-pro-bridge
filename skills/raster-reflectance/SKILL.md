---
name: raster-reflectance
name_en: 影像反射率（辐射定标）计算
name_zh: 影像反射率（辐射定标）计算
description: 读取影像元数据（辐射定标参数、太阳高度角等）把 DN 值转换为辐射亮度或地表反射率，支持选择传感器类型、是否保留辐射亮度与缩放因子，可按需指定波段。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 影像反射率（辐射定标）计算 or similar operations.
description_en: 读取影像元数据（辐射定标参数、太阳高度角等）把 DN 值转换为辐射亮度或地表反射率，支持选择传感器类型、是否保留辐射亮度与缩放因子，可按需指定波段。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 影像反射率（辐射定标）计算 or similar operations.
description_zh: 读取影像元数据（辐射定标参数、太阳高度角等）把 DN 值转换为辐射亮度或地表反射率，支持选择传感器类型、是否保留辐射亮度与缩放因子，可按需指定波段。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「影像反射率（辐射定标）计算」或同类操作时使用。
argument-hint: <输入工作空间> <影像元数据文件路径> <传感器/影像类型> <是否保留辐射亮度> <缩放因子> <波段清单>
argument-hint-en: <输入工作空间> <影像元数据文件路径> <传感器/影像类型> <是否保留辐射亮度> <缩放因子> <波段清单>
argument-hint-zh: <输入工作空间> <影像元数据文件路径> <传感器/影像类型> <是否保留辐射亮度> <缩放因子> <波段清单>
user-invocable: true
---

# 影像反射率（辐射定标）计算

## 功能
读取影像元数据（辐射定标参数、太阳高度角等）把 DN 值转换为辐射亮度或地表反射率，支持选择传感器类型、是否保留辐射亮度与缩放因子，可按需指定波段。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入工作空间
- 影像元数据文件路径
- 传感器/影像类型
- 是否保留辐射亮度
- 缩放因子
- 波段清单
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入工作空间（原参数名：workspace）
2. 影像元数据文件路径（原参数名：metadataPath）
3. 传感器/影像类型（原参数名：SIType）
4. 是否保留辐射亮度（原参数名：keepRad）
5. 缩放因子（原参数名：scaleFactor）
6. 波段清单（原参数名：bandList）

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
python scripts\run.py <输入工作空间> <影像元数据文件路径> <传感器/影像类型> <是否保留辐射亮度> <缩放因子> <波段清单>
```
参数说明：

1. 输入工作空间（原参数名：workspace）
2. 影像元数据文件路径（原参数名：metadataPath）
3. 传感器/影像类型（原参数名：SIType）
4. 是否保留辐射亮度（原参数名：keepRad）
5. 缩放因子（原参数名：scaleFactor）
6. 波段清单（原参数名：bandList）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
