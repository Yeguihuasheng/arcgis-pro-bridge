---
name: stats-numerical-spatial-join
name_en: 数值汇总空间连接
name_zh: 数值汇总空间连接
description: 把连接要素的数值字段按空间关系汇总（求和/均值/中位数/众数/标准差/最小/最大/极差/计数等）写到目标要素上，字段名可加前缀，用于按单元汇总 POI 数、人口数。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 数值汇总空间连接 or similar operations.
description_en: 把连接要素的数值字段按空间关系汇总（求和/均值/中位数/众数/标准差/最小/最大/极差/计数等）写到目标要素上，字段名可加前缀，用于按单元汇总 POI 数、人口数。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 数值汇总空间连接 or similar operations.
description_zh: 把连接要素的数值字段按空间关系汇总（求和/均值/中位数/众数/标准差/最小/最大/极差/计数等）写到目标要素上，字段名可加前缀，用于按单元汇总 POI 数、人口数。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「数值汇总空间连接」或同类操作时使用。
argument-hint: <目标要素类> <连接要素类> <输出要素类> <汇总字段名前缀> <汇总方式（求和/均值等）> <param5> <匹配方式（INTERSECT 等）> <搜索半径>
argument-hint-en: <目标要素类> <连接要素类> <输出要素类> <汇总字段名前缀> <汇总方式（求和/均值等）> <param5> <匹配方式（INTERSECT 等）> <搜索半径>
argument-hint-zh: <目标要素类> <连接要素类> <输出要素类> <汇总字段名前缀> <汇总方式（求和/均值等）> <param5> <匹配方式（INTERSECT 等）> <搜索半径>
user-invocable: true
---

# 数值汇总空间连接

## 功能
把连接要素的数值字段按空间关系汇总（求和/均值/中位数/众数/标准差/最小/最大/极差/计数等）写到目标要素上，字段名可加前缀，用于按单元汇总 POI 数、人口数。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 目标要素类
- 连接要素类
- 输出要素类
- 汇总字段名前缀
- 汇总方式（求和/均值等）
- param5
- 匹配方式（INTERSECT 等）
- 搜索半径
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 目标要素类（原参数名：target_feature_class）
2. 连接要素类（原参数名：join_feature_class）
3. 输出要素类（原参数名：output_feature_Class）
4. 汇总字段名前缀（原参数名：prepended_field_name）
5. 汇总方式（求和/均值等）（原参数名：join_operation）
6. param5（原参数名：param5）
7. 匹配方式（INTERSECT 等）（原参数名：match_option）
8. 搜索半径（原参数名：search_radius）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按上表顺序传入）。
运行环境：ArcGIS Pro

## 执行后复核
- 读回输出的行数/字段值或打开结果文件抽查 3 项；
- 报错时看 traceback 定位到具体参数。

## 详细说明
第 1~8 个参数依次是：目标要素类、连接要素类、输出要素类、字段名前缀、汇总方式、连接类型（true=KEEP_ALL）、匹配方式、搜索半径；第 9 个参数起可再追加最多 11 个「字段清单」（分号分隔），依次对应 SUM/MEAN/MEDIAN/MODE/STD/MIN/MAX/RANGE/COUNT/FIRST/LAST 十一种汇总方式，不需要的方式留空即可；不存在的字段会被自动忽略。

## 参数与调用
```bat
python scripts\run.py <目标要素类> <连接要素类> <输出要素类> <汇总字段名前缀> <汇总方式（求和/均值等）> <param5> <匹配方式（INTERSECT 等）> <搜索半径>
```
参数说明：

1. 目标要素类（原参数名：target_feature_class）
2. 连接要素类（原参数名：join_feature_class）
3. 输出要素类（原参数名：output_feature_Class）
4. 汇总字段名前缀（原参数名：prepended_field_name）
5. 汇总方式（求和/均值等）（原参数名：join_operation）
6. param5（原参数名：param5）
7. 匹配方式（INTERSECT 等）（原参数名：match_option）
8. 搜索半径（原参数名：search_radius）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
