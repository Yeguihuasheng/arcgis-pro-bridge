---
name: plan-yd-statistic
name_en: 用地用海分类统计表
name_zh: 用地用海分类统计表
description: 按用地用海分类代码汇总图斑数与面积，输出一张表：分类代码、分类名称、图斑数、平方米 / 亩 / 公顷、占比。可选择「按一级类汇总」只看到大类，也可以按二级类明细。面积自动按坐标系切换测地面积，避免在地理坐标系下算成平方度。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 用地用海分类统计表 or similar operations.
description_en: 按用地用海分类代码汇总图斑数与面积，输出一张表：分类代码、分类名称、图斑数、平方米 / 亩 / 公顷、占比。可选择「按一级类汇总」只看到大类，也可以按二级类明细。面积自动按坐标系切换测地面积，避免在地理坐标系下算成平方度。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 用地用海分类统计表 or similar operations.
description_zh: 按用地用海分类代码汇总图斑数与面积，输出一张表：分类代码、分类名称、图斑数、平方米 / 亩 / 公顷、占比。可选择「按一级类汇总」只看到大类，也可以按二级类明细。面积自动按坐标系切换测地面积，避免在地理坐标系下算成平方度。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「用地用海分类统计表」或同类操作时使用。
argument-hint: <输入用地图层> <代码字段名（如 YDYHFLDM / DLBM）> <输出统计表 csv> <是否按一级类汇总（是/否）>
argument-hint-en: <输入用地图层> <代码字段名（如 YDYHFLDM / DLBM）> <输出统计表 csv> <是否按一级类汇总（是/否）>
argument-hint-zh: <输入用地图层> <代码字段名（如 YDYHFLDM / DLBM）> <输出统计表 csv> <是否按一级类汇总（是/否）>
user-invocable: true
---

# 用地用海分类统计表

## 功能
按用地用海分类代码汇总图斑数与面积，输出一张表：分类代码、分类名称、图斑数、平方米 / 亩 / 公顷、占比。可选择「按一级类汇总」只看到大类，也可以按二级类明细。面积自动按坐标系切换测地面积，避免在地理坐标系下算成平方度。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入用地图层
- 代码字段名（如 YDYHFLDM / DLBM）
- 输出统计表 csv
- 是否按一级类汇总（是/否）
- 输出位置（GDB 要素类 / csv 路径）
- 坐标系要求：涉及面积时必须确认是否为投影坐标系（脚本已自动按坐标系切换测地面积）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 读回输出图层行数/字段值或打开结果表抽查 3 项与预期一致；
- 报出的「待人工细分」「问题清单」必须原样反馈给用户，不要自行取舍。

## 参数与调用
```bat
python scripts\run.py <输入用地图层> <代码字段名（如 YDYHFLDM / DLBM）> <输出统计表 csv> <是否按一级类汇总（是/否）>
```

## 来源
来自公开开源工具箱的业务口径整理，已去除原作者与界面可见信息；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
