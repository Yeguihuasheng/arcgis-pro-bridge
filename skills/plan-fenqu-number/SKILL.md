---
name: plan-fenqu-number
name_en: 用途分区编号生成
name_zh: 用途分区编号生成
description: 按空间位置（自西向东、自北向南）给用途分区图斑生成连续编号并写入字段，同时可输出分区面积表。对应原工具箱的「用途分区编号生成 / 用途分区规划图生成」。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 用途分区编号生成 or similar operations.
description_en: 按空间位置（自西向东、自北向南）给用途分区图斑生成连续编号并写入字段，同时可输出分区面积表。对应原工具箱的「用途分区编号生成 / 用途分区规划图生成」。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 用途分区编号生成 or similar operations.
description_zh: 按空间位置（自西向东、自北向南）给用途分区图斑生成连续编号并写入字段，同时可输出分区面积表。对应原工具箱的「用途分区编号生成 / 用途分区规划图生成」。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「用途分区编号生成」或同类操作时使用。
argument-hint: <分区图层> <编号字段名（默认 FQBH）> <编号前缀（可留空）> <输出面积表 CSV（留空则不输出）>
argument-hint-en: <分区图层> <编号字段名（默认 FQBH）> <编号前缀（可留空）> <输出面积表 CSV（留空则不输出）>
argument-hint-zh: <分区图层> <编号字段名（默认 FQBH）> <编号前缀（可留空）> <输出面积表 CSV（留空则不输出）>
user-invocable: true
---

# 用途分区编号生成

## 功能
按空间位置（自西向东、自北向南）给用途分区图斑生成连续编号并写入字段，同时可输出分区面积表。对应原工具箱的「用途分区编号生成 / 用途分区规划图生成」。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 分区图层
- 编号字段名（默认 FQBH）
- 编号前缀（可留空）
- 输出面积表 CSV（留空则不输出）
- 输出位置（GDB 要素类 / csv 路径）
- 坐标系要求：涉及面积时必须确认是否为投影坐标系（脚本已自动按坐标系切换测地面积）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 读回输出图层行数/字段值或打开结果表抽查 3 项与预期一致；
- 报出的「待人工细分」「问题清单」必须原样反馈给用户，不要自行取舍。

## 参数与调用
```bat
python scripts\run.py <分区图层> <编号字段名（默认 FQBH）> <编号前缀（可留空）> <输出面积表 CSV（留空则不输出）>
```

## 来源
来自公开开源工具箱的业务口径整理，已去除原作者与界面可见信息；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
