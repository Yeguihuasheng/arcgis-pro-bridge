---
name: tool-batch-split-by-field
name_en: 按字段值拆分图层
name_zh: 按字段值拆分图层
description: 按某个字段的取值把一个图层拆成多个图层，每个取值导出一份（如按行政村名、按用地大类、按批次号拆分）。可自定义输出名前缀，导出后汇报每个取值的要素数，空值会单独归到「空值」一组并提示。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按字段值拆分图层 or similar operations.
description_en: 按某个字段的取值把一个图层拆成多个图层，每个取值导出一份（如按行政村名、按用地大类、按批次号拆分）。可自定义输出名前缀，导出后汇报每个取值的要素数，空值会单独归到「空值」一组并提示。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按字段值拆分图层 or similar operations.
description_zh: 按某个字段的取值把一个图层拆成多个图层，每个取值导出一份（如按行政村名、按用地大类、按批次号拆分）。可自定义输出名前缀，导出后汇报每个取值的要素数，空值会单独归到「空值」一组并提示。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「按字段值拆分图层」或同类操作时使用。
argument-hint: <输入图层> <拆分字段名> <输出工作空间> <输出名前缀（可留空）>
argument-hint-en: <输入图层> <拆分字段名> <输出工作空间> <输出名前缀（可留空）>
argument-hint-zh: <输入图层> <拆分字段名> <输出工作空间> <输出名前缀（可留空）>
user-invocable: true
---

# 按字段值拆分图层

## 功能
按某个字段的取值把一个图层拆成多个图层，每个取值导出一份（如按行政村名、按用地大类、按批次号拆分）。可自定义输出名前缀，导出后汇报每个取值的要素数，空值会单独归到「空值」一组并提示。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入图层
- 拆分字段名
- 输出工作空间
- 输出名前缀（可留空）
- 输出位置（GDB 要素类 / csv 路径）
- 坐标系要求：涉及面积时必须确认是否为投影坐标系（脚本已自动按坐标系切换测地面积）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 读回输出图层行数/字段值或打开结果表抽查 3 项与预期一致；
- 报出的「待人工细分」「问题清单」必须原样反馈给用户，不要自行取舍。

## 参数与调用
```bat
python scripts\run.py <输入图层> <拆分字段名> <输出工作空间> <输出名前缀（可留空）>
```

## 来源
来自公开开源工具箱的业务口径整理，已去除原作者与界面可见信息；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
