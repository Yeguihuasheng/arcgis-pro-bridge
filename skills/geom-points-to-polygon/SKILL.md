---
name: geom-points-to-polygon
name_en: 点集连成面
name_zh: 点集连成面
description: 按分组字段与排序字段把点要素依次连接成面要素（点序即面边界顺序），用于把实测点串还原成地块。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 点集连成面 or similar operations.
description_en: 按分组字段与排序字段把点要素依次连接成面要素（点序即面边界顺序），用于把实测点串还原成地块。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 点集连成面 or similar operations.
description_zh: 按分组字段与排序字段把点要素依次连接成面要素（点序即面边界顺序），用于把实测点串还原成地块。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「点集连成面」或同类操作时使用。
argument-hint: <输入点要素类> <输出点要素类> <分组字段名> <sort_field_name>
argument-hint-en: <输入点要素类> <输出点要素类> <分组字段名> <sort_field_name>
argument-hint-zh: <输入点要素类> <输出点要素类> <分组字段名> <sort_field_name>
user-invocable: true
---

# 点集连成面

## 功能
按分组字段与排序字段把点要素依次连接成面要素（点序即面边界顺序），用于把实测点串还原成地块。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入点要素类
- 输出点要素类
- 分组字段名
- sort_field_name
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入点要素类（原参数名：in_pt_fc）
2. 输出点要素类（原参数名：out_pt_fc）
3. 分组字段名（原参数名：group_field_name）
4. sort_field_name（原参数名：sort_field_name）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按上表顺序传入）。
运行环境：ArcGIS Pro

## 执行后复核
- 读回输出的行数/字段值或打开结果文件抽查 3 项；
- 报错时看 traceback 定位到具体参数。

## 详细说明
第 3 个参数 group_field_name 是分组字段名，第 4 个 sort_field_name 是组内点的排序字段；两处都填同一个字段即可按该字段分组并按其顺序连点成面。

## 参数与调用
```bat
python scripts\run.py <输入点要素类> <输出点要素类> <分组字段名> <sort_field_name>
```
参数说明：

1. 输入点要素类（原参数名：in_pt_fc）
2. 输出点要素类（原参数名：out_pt_fc）
3. 分组字段名（原参数名：group_field_name）
4. sort_field_name（原参数名：sort_field_name）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
