---
name: plan-cad-import
name_en: 从 CAD 导入（DWG 转 GDB）
name_zh: 从 CAD 导入（DWG 转 GDB）
description: 把设计院给的 DWG 转成 GDB 要素数据集，按 CAD 图层拆成点线面注记四类，并汇报每个图层要素数，方便判断哪些层是可用地形、哪些是图框装饰。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 从 CAD 导入（DWG 转 GDB） or similar operations.
description_en: 把设计院给的 DWG 转成 GDB 要素数据集，按 CAD 图层拆成点线面注记四类，并汇报每个图层要素数，方便判断哪些层是可用地形、哪些是图框装饰。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 从 CAD 导入（DWG 转 GDB） or similar operations.
description_zh: 把设计院给的 DWG 转成 GDB 要素数据集，按 CAD 图层拆成点线面注记四类，并汇报每个图层要素数，方便判断哪些层是可用地形、哪些是图框装饰。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「从 CAD 导入（DWG 转 GDB）」或同类操作时使用。
argument-hint: <输入 DWG 路径> <输出 GDB（工作空间）> <输出要素数据集名> <参考比例尺（默认 1000）>
argument-hint-en: <输入 DWG 路径> <输出 GDB（工作空间）> <输出要素数据集名> <参考比例尺（默认 1000）>
argument-hint-zh: <输入 DWG 路径> <输出 GDB（工作空间）> <输出要素数据集名> <参考比例尺（默认 1000）>
user-invocable: true
---

# 从 CAD 导入（DWG 转 GDB）

## 功能
把设计院给的 DWG 转成 GDB 要素数据集，按 CAD 图层拆成点线面注记四类，并汇报每个图层要素数，方便判断哪些层是可用地形、哪些是图框装饰。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入 DWG 路径
- 输出 GDB（工作空间）
- 输出要素数据集名
- 参考比例尺（默认 1000）
- 输出位置（GDB 要素类 / csv 路径）
- 坐标系要求：涉及面积时必须确认是否为投影坐标系（脚本已自动按坐标系切换测地面积）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 读回输出图层行数/字段值或打开结果表抽查 3 项与预期一致；
- 报出的「待人工细分」「问题清单」必须原样反馈给用户，不要自行取舍。

## 参数与调用
```bat
python scripts\run.py <输入 DWG 路径> <输出 GDB（工作空间）> <输出要素数据集名> <参考比例尺（默认 1000）>
```

## 来源
来自公开开源工具箱的业务口径整理，已去除原作者与界面可见信息；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
