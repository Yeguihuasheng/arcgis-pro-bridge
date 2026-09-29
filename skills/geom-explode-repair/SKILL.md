---
name: geom-explode-repair
name_en: 多部件打散与几何修复
name_zh: 多部件打散与几何修复
description: 把多部件要素打散成单部件（一个图斑一个面），可选顺带跑一次几何修复并删掉空几何。多部件在用地统计、图斑编号、拓扑检查里经常出问题，入库前一般都要先打散。打散后汇报前后要素数变化。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 多部件打散与几何修复 or similar operations.
description_en: 把多部件要素打散成单部件（一个图斑一个面），可选顺带跑一次几何修复并删掉空几何。多部件在用地统计、图斑编号、拓扑检查里经常出问题，入库前一般都要先打散。打散后汇报前后要素数变化。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 多部件打散与几何修复 or similar operations.
description_zh: 把多部件要素打散成单部件（一个图斑一个面），可选顺带跑一次几何修复并删掉空几何。多部件在用地统计、图斑编号、拓扑检查里经常出问题，入库前一般都要先打散。打散后汇报前后要素数变化。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「多部件打散与几何修复」或同类操作时使用。
argument-hint: <输入要素类> <输出要素类> <是否同时修复几何（是/否）>
argument-hint-en: <输入要素类> <输出要素类> <是否同时修复几何（是/否）>
argument-hint-zh: <输入要素类> <输出要素类> <是否同时修复几何（是/否）>
user-invocable: true
---

# 多部件打散与几何修复

## 功能
把多部件要素打散成单部件（一个图斑一个面），可选顺带跑一次几何修复并删掉空几何。多部件在用地统计、图斑编号、拓扑检查里经常出问题，入库前一般都要先打散。打散后汇报前后要素数变化。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入要素类
- 输出要素类
- 是否同时修复几何（是/否）
- 输出位置（GDB 要素类 / csv 路径）
- 坐标系要求：涉及面积时必须确认是否为投影坐标系（脚本已自动按坐标系切换测地面积）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 读回输出图层行数/字段值或打开结果表抽查 3 项与预期一致；
- 报出的「待人工细分」「问题清单」必须原样反馈给用户，不要自行取舍。

## 参数与调用
```bat
python scripts\run.py <输入要素类> <输出要素类> <是否同时修复几何（是/否）>
```

## 来源
来自公开开源工具箱的业务口径整理，已去除原作者与界面可见信息；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
