---
name: plan-cad-export
name_en: 导出到 CAD（DWG）
name_zh: 导出到 CAD（DWG）
description: 把规划图层导出成 DWG，方便与设计院在 CAD 里对接。可一次导多个图层，按 DWG R2010 格式输出；多部件、注记、字段名长度等 CAD 限制会一并提醒。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 导出到 CAD（DWG） or similar operations.
description_en: 把规划图层导出成 DWG，方便与设计院在 CAD 里对接。可一次导多个图层，按 DWG R2010 格式输出；多部件、注记、字段名长度等 CAD 限制会一并提醒。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 导出到 CAD（DWG） or similar operations.
description_zh: 把规划图层导出成 DWG，方便与设计院在 CAD 里对接。可一次导多个图层，按 DWG R2010 格式输出；多部件、注记、字段名长度等 CAD 限制会一并提醒。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「导出到 CAD（DWG）」或同类操作时使用。
argument-hint: <输入图层（多个用英文分号 ; 分隔）> <输出 DWG 路径> <需保留的字段（逗号分隔，可空）> <是否只导面（是/否）>
argument-hint-en: <输入图层（多个用英文分号 ; 分隔）> <输出 DWG 路径> <需保留的字段（逗号分隔，可空）> <是否只导面（是/否）>
argument-hint-zh: <输入图层（多个用英文分号 ; 分隔）> <输出 DWG 路径> <需保留的字段（逗号分隔，可空）> <是否只导面（是/否）>
user-invocable: true
---

# 导出到 CAD（DWG）

## 功能
把规划图层导出成 DWG，方便与设计院在 CAD 里对接。可一次导多个图层，按 DWG R2010 格式输出；多部件、注记、字段名长度等 CAD 限制会一并提醒。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入图层（多个用英文分号 ; 分隔）
- 输出 DWG 路径
- 需保留的字段（逗号分隔，可空）
- 是否只导面（是/否）
- 输出位置（GDB 要素类 / csv 路径）
- 坐标系要求：涉及面积时必须确认是否为投影坐标系（脚本已自动按坐标系切换测地面积）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 读回输出图层行数/字段值或打开结果表抽查 3 项与预期一致；
- 报出的「待人工细分」「问题清单」必须原样反馈给用户，不要自行取舍。

## 参数与调用
```bat
python scripts\run.py <输入图层（多个用英文分号 ; 分隔）> <输出 DWG 路径> <需保留的字段（逗号分隔，可空）> <是否只导面（是/否）>
```

## 来源
来自公开开源工具箱的业务口径整理，已去除原作者与界面可见信息；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
