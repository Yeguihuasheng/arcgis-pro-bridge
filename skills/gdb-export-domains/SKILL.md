---
name: gdb-export-domains
name_en: 导出属性域值清单
name_zh: 导出属性域值清单
description: 把地理数据库内所有「编码值属性域」（coded value domain）导出为同名表（写到该 GDB 内），可选再转成 Excel。用于属性域字典存档、跨库迁移、对外提供码表。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_en: 把地理数据库内所有「编码值属性域」（coded value domain）导出为同名表（写到该 GDB 内），可选再转成 Excel。用于属性域字典存档、跨库迁移、对外提供码表。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_zh: 把地理数据库内所有「编码值属性域」（coded value domain）导出为同名表（写到该 GDB 内），可选再转成 Excel。用于属性域字典存档、跨库迁移、对外提供码表。经 YghsBridge MCP 在 ArcGIS Pro 内执行。
argument-hint: <输入工作空间（GDB）> [是否另存 Excel true/false 默认 false]
argument-hint-en: <输入工作空间（GDB）> [是否另存 Excel true/false 默认 false]
argument-hint-zh: <输入工作空间（GDB）> [是否另存 Excel true/false 默认 false]
user-invocable: true
---

# 导出属性域值清单

## 功能
把地理数据库内所有「编码值属性域」导出为同名表（写到该 GDB 内），可选再转成 Excel。用于属性域字典存档、跨库迁移、对外提供码表。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入工作空间（GDB 路径）
- 是否另存 Excel（true/false，默认 false）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 抽查 GDB 内新增的属性域表，核对「编码-描述」与属性域定义一致；
- 若勾选 Excel，确认输出 .xls 文件内容正确。

## 参数与调用
```bat
python scripts\run.py <输入工作空间（GDB）> [是否另存Excel true/false]
```

## 来源
来自 X/MIT 许可的开源脚本（export_gdb_domains）的业务口径整理；原始出处与许可证见
仓库根目录 `ATTRIBUTION.md`。
