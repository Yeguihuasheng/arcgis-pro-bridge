---
name: plan-base-convert
name_en: 三调基数转换（DLBM→用地用海）
name_zh: 三调基数转换（DLBM→用地用海）
description: 按《国土空间调查、规划、用途管制用地用海分类指南》的衔接关系，把三调地类图斑的DLBM 编码换算为用地用海分类，一次写入：一级代码、一级名称、分类代码、分类名称。一对多需要细分的编码（如 05H1、08H2）会单独报出来，提醒人工判定。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 三调基数转换（DLBM→用地用海） or similar operations.
description_en: 按《国土空间调查、规划、用途管制用地用海分类指南》的衔接关系，把三调地类图斑的DLBM 编码换算为用地用海分类，一次写入：一级代码、一级名称、分类代码、分类名称。一对多需要细分的编码（如 05H1、08H2）会单独报出来，提醒人工判定。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 三调基数转换（DLBM→用地用海） or similar operations.
description_zh: 按《国土空间调查、规划、用途管制用地用海分类指南》的衔接关系，把三调地类图斑的DLBM 编码换算为用地用海分类，一次写入：一级代码、一级名称、分类代码、分类名称。一对多需要细分的编码（如 05H1、08H2）会单独报出来，提醒人工判定。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「三调基数转换（DLBM→用地用海）」或同类操作时使用。
argument-hint: <输入图层（三调地类图斑，含 DLBM）> <输出要素类> <DLBM 字段名（默认 DLBM）> <是否只保留 DLBM/DLMC 两个字段（是/否，默认 是）>
argument-hint-en: <输入图层（三调地类图斑，含 DLBM）> <输出要素类> <DLBM 字段名（默认 DLBM）> <是否只保留 DLBM/DLMC 两个字段（是/否，默认 是）>
argument-hint-zh: <输入图层（三调地类图斑，含 DLBM）> <输出要素类> <DLBM 字段名（默认 DLBM）> <是否只保留 DLBM/DLMC 两个字段（是/否，默认 是）>
user-invocable: true
---

# 三调基数转换（DLBM→用地用海）

## 功能
按《国土空间调查、规划、用途管制用地用海分类指南》的衔接关系，把三调地类图斑的DLBM 编码换算为用地用海分类，一次写入：一级代码、一级名称、分类代码、分类名称。一对多需要细分的编码（如 05H1、08H2）会单独报出来，提醒人工判定。

口径提醒（重要）：带 H 与多义编码（05H1、08H1、08H2、0810A 等）在各省细则里归属并不一致，例如《安徽省村庄规划编制指南》附录D 把 05H1 部分归入「城镇社区服务设施用地」「农村社区服务设施用地」。本表按常用衔接关系给出，跑完必须拿当地指南复核报出来的待细分清单，不能直接当成果交。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入图层（三调地类图斑，含 DLBM）
- 输出要素类
- DLBM 字段名（默认 DLBM）
- 是否只保留 DLBM/DLMC 两个字段（是/否，默认 是）
- 输出位置（GDB 要素类 / csv 路径）
- 坐标系要求：涉及面积时必须确认是否为投影坐标系（脚本已自动按坐标系切换测地面积）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 读回输出图层行数/字段值或打开结果表抽查 3 项与预期一致；
- 报出的「待人工细分」「问题清单」必须原样反馈给用户，不要自行取舍。

## 参数与调用
```bat
python scripts\run.py <输入图层（三调地类图斑，含 DLBM）> <输出要素类> <DLBM 字段名（默认 DLBM）> <是否只保留 DLBM/DLMC 两个字段（是/否，默认 是）>
```

## 来源
来自公开开源工具箱的业务口径整理，已去除原作者与界面可见信息；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
