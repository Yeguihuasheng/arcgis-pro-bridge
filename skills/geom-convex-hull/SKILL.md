---
name: geom-convex-hull
name_en: 生成凸包
name_zh: 生成凸包
description: 按分组字段为点要素生成凸包（可再按指定距离外扩成缓冲区），输出面要素，常用于求点群的外围轮廓与最小包络范围。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 生成凸包 or similar operations.
description_en: 按分组字段为点要素生成凸包（可再按指定距离外扩成缓冲区），输出面要素，常用于求点群的外围轮廓与最小包络范围。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 生成凸包 or similar operations.
description_zh: 按分组字段为点要素生成凸包（可再按指定距离外扩成缓冲区），输出面要素，常用于求点群的外围轮廓与最小包络范围。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「生成凸包」或同类操作时使用。
argument-hint: <输入点要素类> <输出点要素类> <分组字段> <分组字段名> <是否再生成外缓冲> <外缓冲距离>
argument-hint-en: <输入点要素类> <输出点要素类> <分组字段> <分组字段名> <是否再生成外缓冲> <外缓冲距离>
argument-hint-zh: <输入点要素类> <输出点要素类> <分组字段> <分组字段名> <是否再生成外缓冲> <外缓冲距离>
user-invocable: true
---

# 生成凸包

## 功能
按分组字段为点要素生成凸包（可再按指定距离外扩成缓冲区），输出面要素，常用于求点群的外围轮廓与最小包络范围。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入点要素类
- 输出点要素类
- 分组字段
- 分组字段名
- 是否再生成外缓冲
- 外缓冲距离
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入点要素类（原参数名：in_pt_fc）
2. 输出点要素类（原参数名：out_pt_fc）
3. 分组字段（原参数名：group_field）
4. 分组字段名（原参数名：group_field_name）
5. 是否再生成外缓冲（原参数名：create_buffer）
6. 外缓冲距离（原参数名：buffer_num）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按上表顺序传入）。
运行环境：ArcGIS Pro

## 执行后复核
- 读回输出的行数/字段值或打开结果文件抽查 3 项；
- 报错时看 traceback 定位到具体参数。

## 详细说明
第 3 个参数 group_field 是「是否按字段分组」的布尔值（true/false），第 4 个 group_field_name 才是分组字段名；第 5 个 create_buffer 为 true 时按第 6 个 buffer_num 缓冲外扩，为 false 时直接输出凸包面。

## 参数与调用
```bat
python scripts\run.py <输入点要素类> <输出点要素类> <分组字段> <分组字段名> <是否再生成外缓冲> <外缓冲距离>
```
参数说明：

1. 输入点要素类（原参数名：in_pt_fc）
2. 输出点要素类（原参数名：out_pt_fc）
3. 分组字段（原参数名：group_field）
4. 分组字段名（原参数名：group_field_name）
5. 是否再生成外缓冲（原参数名：create_buffer）
6. 外缓冲距离（原参数名：buffer_num）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
