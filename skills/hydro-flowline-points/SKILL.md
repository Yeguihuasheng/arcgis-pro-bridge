---
name: hydro-flowline-points
name_en: 流线纵剖面点生成
name_zh: 流线纵剖面点生成
description: 以距河口距离为量测值把流线建成路由，再按间距生成带三维高程的河流纵剖面点，用于绘制纵剖面与水面线。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 流线纵剖面点生成 or similar operations.
description_en: 以距河口距离为量测值把流线建成路由，再按间距生成带三维高程的河流纵剖面点，用于绘制纵剖面与水面线。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 流线纵剖面点生成 or similar operations.
description_zh: 以距河口距离为量测值把流线建成路由，再按间距生成带三维高程的河流纵剖面点，用于绘制纵剖面与水面线。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「流线纵剖面点生成」或同类操作时使用。
argument-hint: <输出要素数据集> <输入流线要素类> <输入 DEM 栅格> <距河口距离（km）> <站点间距> <校准点要素类> <点 ID 字段> <量测字段> <搜索半径>
argument-hint-en: <输出要素数据集> <输入流线要素类> <输入 DEM 栅格> <距河口距离（km）> <站点间距> <校准点要素类> <点 ID 字段> <量测字段> <搜索半径>
argument-hint-zh: <输出要素数据集> <输入流线要素类> <输入 DEM 栅格> <距河口距离（km）> <站点间距> <校准点要素类> <点 ID 字段> <量测字段> <搜索半径>
user-invocable: true
---

# 流线纵剖面点生成

## 功能
以距河口距离为量测值把流线建成路由，再按间距生成带三维高程的河流纵剖面点，用于绘制纵剖面与水面线。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输出要素数据集
- 输入流线要素类
- 输入 DEM 栅格
- 距河口距离（km）
- 站点间距
- 校准点要素类
- 点 ID 字段
- 量测字段
- 搜索半径
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输出要素数据集（原参数名：feature_dataset）
2. 输入流线要素类（原参数名：flowline）
3. 输入 DEM 栅格（原参数名：dem）
4. 距河口距离（km）（原参数名：km_to_mouth）
5. 站点间距（原参数名：station_distance）
6. 校准点要素类（原参数名：calibration_points）
7. 点 ID 字段（原参数名：point_id_field）
8. 量测字段（原参数名：measure_field）
9. 搜索半径（原参数名：search_radius）

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
python scripts\run.py <输出要素数据集> <输入流线要素类> <输入 DEM 栅格> <距河口距离（km）> <站点间距> <校准点要素类> <点 ID 字段> <量测字段> <搜索半径>
```
参数说明：

1. 输出要素数据集（原参数名：feature_dataset）
2. 输入流线要素类（原参数名：flowline）
3. 输入 DEM 栅格（原参数名：dem）
4. 距河口距离（km）（原参数名：km_to_mouth）
5. 站点间距（原参数名：station_distance）
6. 校准点要素类（原参数名：calibration_points）
7. 点 ID 字段（原参数名：point_id_field）
8. 量测字段（原参数名：measure_field）
9. 搜索半径（原参数名：search_radius）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
