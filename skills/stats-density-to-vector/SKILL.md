---
name: stats-density-to-vector
name_en: 核密度估值回写矢量
name_zh: 核密度估值回写矢量
description: 对点要素做核密度分析并把密度值提取回写（可沿网络），用于热度评估、密度图量化到单元。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 核密度估值回写矢量 or similar operations.
description_en: 对点要素做核密度分析并把密度值提取回写（可沿网络），用于热度评估、密度图量化到单元。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 核密度估值回写矢量 or similar operations.
description_zh: 对点要素做核密度分析并把密度值提取回写（可沿网络），用于热度评估、密度图量化到单元。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「核密度估值回写矢量」或同类操作时使用。
argument-hint: <输入点要素类> <weighted_fields> <输入网络数据集（可选）> <percentile_bool> <密度值写入字段名> <输出栅格像元大小> <搜索半径> <area_unit_factor> <percentage_sample> <group_by_stat> <障碍要素类（可选）> <中间栅格输出（可选）>
argument-hint-en: <输入点要素类> <weighted_fields> <输入网络数据集（可选）> <percentile_bool> <密度值写入字段名> <输出栅格像元大小> <搜索半径> <area_unit_factor> <percentage_sample> <group_by_stat> <障碍要素类（可选）> <中间栅格输出（可选）>
argument-hint-zh: <输入点要素类> <weighted_fields> <输入网络数据集（可选）> <percentile_bool> <密度值写入字段名> <输出栅格像元大小> <搜索半径> <area_unit_factor> <percentage_sample> <group_by_stat> <障碍要素类（可选）> <中间栅格输出（可选）>
user-invocable: true
---

# 核密度估值回写矢量

## 功能
对点要素做核密度分析并把密度值提取回写（可沿网络），用于热度评估、密度图量化到单元。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入点要素类
- weighted_fields
- 输入网络数据集（可选）
- percentile_bool
- 密度值写入字段名
- 输出栅格像元大小
- 搜索半径
- area_unit_factor
- percentage_sample
- group_by_stat
- 障碍要素类（可选）
- 中间栅格输出（可选）
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入点要素类（原参数名：input_feature_class）
2. weighted_fields（原参数名：weighted_fields）
3. 输入网络数据集（可选）（原参数名：input_network）
4. percentile_bool（原参数名：percentile_bool）
5. 密度值写入字段名（原参数名：field_edit）
6. 输出栅格像元大小（原参数名：cell_size）
7. 搜索半径（原参数名：search_radius）
8. area_unit_factor（原参数名：area_unit_factor）
9. percentage_sample（原参数名：percentage_sample）
10. group_by_stat（原参数名：group_by_stat）
11. 障碍要素类（可选）（原参数名：barrier_fc）
12. 中间栅格输出（可选）（原参数名：intermediate_ra）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按上表顺序传入）。
运行环境：ArcGIS Pro

## 执行后复核
- 读回输出的行数/字段值或打开结果文件抽查 3 项；
- 报错时看 traceback 定位到具体参数。

## 详细说明
依赖 Spatial Analyst 扩展（arcpy.sa.KernelDensity / ExtractValuesToPoints），许可不可用时工具会报错。

## 参数与调用
```bat
python scripts\run.py <输入点要素类> <weighted_fields> <输入网络数据集（可选）> <percentile_bool> <密度值写入字段名> <输出栅格像元大小> <搜索半径> <area_unit_factor> <percentage_sample> <group_by_stat> <障碍要素类（可选）> <中间栅格输出（可选）>
```
参数说明：

1. 输入点要素类（原参数名：input_feature_class）
2. weighted_fields（原参数名：weighted_fields）
3. 输入网络数据集（可选）（原参数名：input_network）
4. percentile_bool（原参数名：percentile_bool）
5. 密度值写入字段名（原参数名：field_edit）
6. 输出栅格像元大小（原参数名：cell_size）
7. 搜索半径（原参数名：search_radius）
8. area_unit_factor（原参数名：area_unit_factor）
9. percentage_sample（原参数名：percentage_sample）
10. group_by_stat（原参数名：group_by_stat）
11. 障碍要素类（可选）（原参数名：barrier_fc）
12. 中间栅格输出（可选）（原参数名：intermediate_ra）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
