---
name: z-interp-missing
name_en: 线要素缺失 Z 值插补
name_zh: 线要素缺失 Z 值插补
description: 对 3D 线（polylineZ）要素，把缺失高程的折点（Z 为 0 或 None）沿线路按已知高程折点做线性插值补全，输出新要素类。用于河网/管线/断面线高程缺漏补全，为纵剖面、三维建模做准备。逐条线独立处理。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_en: 对 3D 线（polylineZ）要素，把缺失高程的折点（Z 为 0 或 None）沿线路按已知高程折点做线性插值补全，输出新要素类。用于河网/管线/断面线高程缺漏补全，为纵剖面、三维建模做准备。逐条线独立处理。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_zh: 对 3D 线（polylineZ）要素，把缺失高程的折点（Z 为 0 或 None）沿线路按已知高程折点做线性插值补全，输出新要素类。用于河网/管线/断面线高程缺漏补全，为纵剖面、三维建模做准备。逐条线独立处理。经 YghsBridge MCP 在 ArcGIS Pro 内执行。
argument-hint: <输入 3D 线要素类（polylineZ）> <输出要素类>
argument-hint-en: <输入 3D 线要素类（polylineZ）> <输出要素类>
argument-hint-zh: <输入 3D 线要素类（polylineZ）> <输出要素类>
user-invocable: true
---

# 线要素缺失 Z 值插补

## 功能
对 3D 线（polylineZ）要素，把缺失高程的折点（Z 为 0 或 None）沿线路按已知高程折点做线性插值补全，输出新要素类。首/尾折点缺高程时沿用最近已知高程；中间缺漏按链长线性内插。用于河网、管线、断面线高程缺漏补全。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入 3D 线要素类（polylineZ，路径或图层名）
- 输出要素类（新路径）
- 缺 Z 的判定口径：默认「Z 为 0 或空」视为缺失（如有特殊阈值请说明）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 抽查 1~2 条线插补前后的折点 Z，确认线性内插值合理、已知高程点未被改动；
- 全无有效高程的线会被原样保留并在日志中计入「未改」。

## 参数与调用
```bat
python scripts\run.py <输入 3D 线要素类> <输出要素类>
```

## 来源
来自 X/MIT 许可的开源脚本（interp_missing_z）的业务口径整理，已按 Pro 环境独立重写
（逐条线处理、不合并线）；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
