---
name: hydro-xs-classify-points
name_en: 横断面点地貌分类
name_zh: 横断面点地貌分类
description: 按断面点落在主槽多边形还是洪泛区多边形（可设缓冲距离）把横断面测点分类为河道/河漫滩等地貌部位，用于断面形态与水力分区统计。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 横断面点地貌分类 or similar operations.
description_en: 按断面点落在主槽多边形还是洪泛区多边形（可设缓冲距离）把横断面测点分类为河道/河漫滩等地貌部位，用于断面形态与水力分区统计。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 横断面点地貌分类 or similar operations.
description_zh: 按断面点落在主槽多边形还是洪泛区多边形（可设缓冲距离）把横断面测点分类为河道/河漫滩等地貌部位，用于断面形态与水力分区统计。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「横断面点地貌分类」或同类操作时使用。
argument-hint: <输出要素数据集> <横断面点要素类> <主槽多边形> <洪泛区多边形> <缓冲距离>
argument-hint-en: <输出要素数据集> <横断面点要素类> <主槽多边形> <洪泛区多边形> <缓冲距离>
argument-hint-zh: <输出要素数据集> <横断面点要素类> <主槽多边形> <洪泛区多边形> <缓冲距离>
user-invocable: true
---

# 横断面点地貌分类

## 功能
按断面点落在主槽多边形还是洪泛区多边形（可设缓冲距离）把横断面测点分类为河道/河漫滩等地貌部位，用于断面形态与水力分区统计。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输出要素数据集
- 横断面点要素类
- 主槽多边形
- 洪泛区多边形
- 缓冲距离
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输出要素数据集（原参数名：feature_dataset）
2. 横断面点要素类（原参数名：xs_points）
3. 主槽多边形（原参数名：channel_polygon）
4. 洪泛区多边形（原参数名：floodplain_polygon）
5. 缓冲距离（原参数名：buffer_distance）

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
python scripts\run.py <输出要素数据集> <横断面点要素类> <主槽多边形> <洪泛区多边形> <缓冲距离>
```
参数说明：

1. 输出要素数据集（原参数名：feature_dataset）
2. 横断面点要素类（原参数名：xs_points）
3. 主槽多边形（原参数名：channel_polygon）
4. 洪泛区多边形（原参数名：floodplain_polygon）
5. 缓冲距离（原参数名：buffer_distance）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
