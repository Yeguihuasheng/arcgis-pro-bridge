---
name: gdb-domains-in-use
name_en: 查找使用中的属性域
name_zh: 查找使用中的属性域
description: 扫描地理数据库内所有要素类与表（含子类型），找出哪些字段引用了属性域，输出「数据集, 子类型, 字段, 属性域」清单 CSV，用于清理冗余属性域、盘点属性域引用关系。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_en: 扫描地理数据库内所有要素类与表（含子类型），找出哪些字段引用了属性域，输出「数据集, 子类型, 字段, 属性域」清单 CSV，用于清理冗余属性域、盘点属性域引用关系。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_zh: 扫描地理数据库内所有要素类与表（含子类型），找出哪些字段引用了属性域，输出「数据集, 子类型, 字段, 属性域」清单 CSV，用于清理冗余属性域、盘点属性域引用关系。经 YghsBridge MCP 在 ArcGIS Pro 内执行。
argument-hint: <输入工作空间（GDB）> <输出 CSV 路径（可空）>
argument-hint-en: <输入工作空间（GDB）> <输出 CSV 路径（可空）>
argument-hint-zh: <输入工作空间（GDB）> <输出 CSV 路径（可空）>
user-invocable: true
---

# 查找使用中的属性域

## 功能
扫描地理数据库内所有要素类与表（含子类型），找出哪些字段引用了属性域，输出「数据集, 子类型, 字段, 属性域」清单，可写入 CSV。用于清理冗余属性域、盘点属性域引用关系。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入工作空间（GDB 路径）
- 输出 CSV 路径（可选，留空则只在日志输出清单）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 抽查 CSV 里某一行，回到 GDB 里确认该字段确实挂了对应属性域；
- 用「导出属性域值清单」交叉核对编码值域内容。

## 参数与调用
```bat
python scripts\run.py <输入工作空间（GDB）> <输出 CSV 路径>
```

## 来源
来自 X/MIT 许可的开源脚本（get-domains-in-use）的业务口径整理，已去掉本机硬编码路径
并增加 CSV 输出；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
