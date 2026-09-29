---
name: table-export-csv-excel
name_en: 属性表导出 CSV / Excel
name_zh: 属性表导出 CSV / Excel
description: 把要素类或表的属性导出成 CSV 或 Excel，供统计、上报、对外交付。可只导出指定字段（留空为全部），CSV 走 UTF-8 带 BOM，Excel 直接打开的中文不会乱码。导出后汇报行数与列数。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 属性表导出 CSV / Excel or similar operations.
description_en: 把要素类或表的属性导出成 CSV 或 Excel，供统计、上报、对外交付。可只导出指定字段（留空为全部），CSV 走 UTF-8 带 BOM，Excel 直接打开的中文不会乱码。导出后汇报行数与列数。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 属性表导出 CSV / Excel or similar operations.
description_zh: 把要素类或表的属性导出成 CSV 或 Excel，供统计、上报、对外交付。可只导出指定字段（留空为全部），CSV 走 UTF-8 带 BOM，Excel 直接打开的中文不会乱码。导出后汇报行数与列数。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「属性表导出 CSV / Excel」或同类操作时使用。
argument-hint: <输入表或要素类> <输出文件（.csv 或 .xls）> <字段（多个用分号分隔，留空为全部）>
argument-hint-en: <输入表或要素类> <输出文件（.csv 或 .xls）> <字段（多个用分号分隔，留空为全部）>
argument-hint-zh: <输入表或要素类> <输出文件（.csv 或 .xls）> <字段（多个用分号分隔，留空为全部）>
user-invocable: true
---

# 属性表导出 CSV / Excel

## 功能
把要素类或表的属性导出成 CSV 或 Excel，供统计、上报、对外交付。可只导出指定字段（留空为全部），CSV 走 UTF-8 带 BOM，Excel 直接打开的中文不会乱码。导出后汇报行数与列数。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入表或要素类
- 输出文件（.csv 或 .xls）
- 字段（多个用分号分隔，留空为全部）
- 输出位置（GDB 要素类 / csv 路径）
- 坐标系要求：涉及面积时必须确认是否为投影坐标系（脚本已自动按坐标系切换测地面积）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 读回输出图层行数/字段值或打开结果表抽查 3 项与预期一致；
- 报出的「待人工细分」「问题清单」必须原样反馈给用户，不要自行取舍。

## 参数与调用
```bat
python scripts\run.py <输入表或要素类> <输出文件（.csv 或 .xls）> <字段（多个用分号分隔，留空为全部）>
```

## 来源
来自公开开源工具箱的业务口径整理，已去除原作者与界面可见信息；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
