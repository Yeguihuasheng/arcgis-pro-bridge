---
name: tool-layer-from-selected
name_en: 选中要素另存为图层
name_zh: 选中要素另存为图层
description: 把图层中「当前选中的要素」复制成一个新的独立要素类/图层（只含选中要素），用于把一次交互选择的结果固化为可复用的数据，替代右键「根据所选要素创建图层」的脚本化版本。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_en: 把图层中「当前选中的要素」复制成一个新的独立要素类/图层（只含选中要素），用于把一次交互选择的结果固化为可复用的数据，替代右键「根据所选要素创建图层」的脚本化版本。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_zh: 把图层中「当前选中的要素」复制成一个新的独立要素类/图层（只含选中要素），用于把一次交互选择的结果固化为可复用的数据，替代右键「根据所选要素创建图层」的脚本化版本。经 YghsBridge MCP 在 ArcGIS Pro 内执行。
argument-hint: <输入图层（含当前选择集）> <输出要素类>
argument-hint-en: <输入图层（含当前选择集）> <输出要素类>
argument-hint-zh: <输入图层（含当前选择集）> <输出要素类>
user-invocable: true
---

# 选中要素另存为图层

## 功能
把图层中「当前选中的要素」复制成一个新的独立要素类/图层（只含选中要素）。用于把一次交互选择的结果固化为可复用的数据，是右键「根据所选要素创建图层」的脚本化版本，便于批量脚本里串联使用。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入图层（须已存在当前选择集，路径或图层名）
- 输出要素类（新路径，避免覆盖已有数据）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 读回输出要素类行数，与选择集要素数一致；
- 若无选择集会直接中止并提示，不会生成空数据。

## 参数与调用
```bat
python scripts\run.py <输入图层> <输出要素类>
```

## 来源
来自 X/MIT 许可的开源脚本（layer_from_selected）的业务口径整理；原始出处与许可证见
仓库根目录 `ATTRIBUTION.md`。
