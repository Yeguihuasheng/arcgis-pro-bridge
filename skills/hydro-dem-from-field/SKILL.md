---
name: hydro-dem-from-field
name_en: 由外业测点生成 DEM
name_zh: 由外业测点生成 DEM
description: 把外业实测的高程点（CSV/点要素）插值成 DEM 栅格，用于缺少现成地形数据、只有实测点时的地形重建。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 由外业测点生成 DEM or similar operations.
description_en: 把外业实测的高程点（CSV/点要素）插值成 DEM 栅格，用于缺少现成地形数据、只有实测点时的地形重建。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 由外业测点生成 DEM or similar operations.
description_zh: 把外业实测的高程点（CSV/点要素）插值成 DEM 栅格，用于缺少现成地形数据、只有实测点时的地形重建。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「由外业测点生成 DEM」或同类操作时使用。
argument-hint: <输出要素数据集> <外业深泓点要素类> <外业横断面点要素类> <插值方法> <输出栅格像元大小> <样条类型> <权重> <参与插值的点数>
argument-hint-en: <输出要素数据集> <外业深泓点要素类> <外业横断面点要素类> <插值方法> <输出栅格像元大小> <样条类型> <权重> <参与插值的点数>
argument-hint-zh: <输出要素数据集> <外业深泓点要素类> <外业横断面点要素类> <插值方法> <输出栅格像元大小> <样条类型> <权重> <参与插值的点数>
user-invocable: true
---

# 由外业测点生成 DEM

## 功能
把外业实测的高程点（CSV/点要素）插值成 DEM 栅格，用于缺少现成地形数据、只有实测点时的地形重建。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输出要素数据集
- 外业深泓点要素类
- 外业横断面点要素类
- 插值方法
- 输出栅格像元大小
- 样条类型
- 权重
- 参与插值的点数
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输出要素数据集（原参数名：feature_dataset）
2. 外业深泓点要素类（原参数名：thalweg_points）
3. 外业横断面点要素类（原参数名：field_xs_points）
4. 插值方法（原参数名：method）
5. 输出栅格像元大小（原参数名：cell_size）
6. 样条类型（原参数名：spline_type）
7. 权重（原参数名：weight）
8. 参与插值的点数（原参数名：number_points）

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
python scripts\run.py <输出要素数据集> <外业深泓点要素类> <外业横断面点要素类> <插值方法> <输出栅格像元大小> <样条类型> <权重> <参与插值的点数>
```
参数说明：

1. 输出要素数据集（原参数名：feature_dataset）
2. 外业深泓点要素类（原参数名：thalweg_points）
3. 外业横断面点要素类（原参数名：field_xs_points）
4. 插值方法（原参数名：method）
5. 输出栅格像元大小（原参数名：cell_size）
6. 样条类型（原参数名：spline_type）
7. 权重（原参数名：weight）
8. 参与插值的点数（原参数名：number_points）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
