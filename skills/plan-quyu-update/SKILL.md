---
name: plan-quyu-update
name_en: 街区/街坊/分村区域更新与检查
name_zh: 街区/街坊/分村区域更新与检查
description: 按区域单元（街区/街坊/分村）统计各类用地面积并回写字段，同时检查区域之间是否存在覆盖缝隙或重叠，输出统计表 CSV。对应原工具箱的「区域更新 / 区域检查」。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 街区/街坊/分村区域更新与检查 or similar operations.
description_en: 按区域单元（街区/街坊/分村）统计各类用地面积并回写字段，同时检查区域之间是否存在覆盖缝隙或重叠，输出统计表 CSV。对应原工具箱的「区域更新 / 区域检查」。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 街区/街坊/分村区域更新与检查 or similar operations.
description_zh: 按区域单元（街区/街坊/分村）统计各类用地面积并回写字段，同时检查区域之间是否存在覆盖缝隙或重叠，输出统计表 CSV。对应原工具箱的「区域更新 / 区域检查」。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「街区/街坊/分村区域更新与检查」或同类操作时使用。
argument-hint: <区域图层（街区/街坊/分村）> <用地图层> <区域编号字段> <用地代码字段（默认 YDYHFLDM，留空则只统计总面积）> <输出统计表 CSV（留空则不输出）>
argument-hint-en: <区域图层（街区/街坊/分村）> <用地图层> <区域编号字段> <用地代码字段（默认 YDYHFLDM，留空则只统计总面积）> <输出统计表 CSV（留空则不输出）>
argument-hint-zh: <区域图层（街区/街坊/分村）> <用地图层> <区域编号字段> <用地代码字段（默认 YDYHFLDM，留空则只统计总面积）> <输出统计表 CSV（留空则不输出）>
user-invocable: true
---

# 街区/街坊/分村区域更新与检查

## 功能
按区域单元（街区/街坊/分村）统计各类用地面积并回写字段，同时检查区域之间是否存在覆盖缝隙或重叠，输出统计表 CSV。对应原工具箱的「区域更新 / 区域检查」。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 区域图层（街区/街坊/分村）
- 用地图层
- 区域编号字段
- 用地代码字段（默认 YDYHFLDM，留空则只统计总面积）
- 输出统计表 CSV（留空则不输出）
- 输出位置（GDB 要素类 / csv 路径）
- 坐标系要求：涉及面积时必须确认是否为投影坐标系（脚本已自动按坐标系切换测地面积）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 读回输出图层行数/字段值或打开结果表抽查 3 项与预期一致；
- 报出的「待人工细分」「问题清单」必须原样反馈给用户，不要自行取舍。

## 参数与调用
```bat
python scripts\run.py <区域图层（街区/街坊/分村）> <用地图层> <区域编号字段> <用地代码字段（默认 YDYHFLDM，留空则只统计总面积）> <输出统计表 CSV（留空则不输出）>
```

## 来源
来自公开开源工具箱的业务口径整理，已去除原作者与界面可见信息；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
