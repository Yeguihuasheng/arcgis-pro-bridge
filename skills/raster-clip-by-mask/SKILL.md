---
name: raster-clip-by-mask
name_en: 影像按范围批量裁剪
name_zh: 影像按范围批量裁剪
description: 用一个矢量范围（如村界、项目红线）批量裁剪一批影像/DEM，输出按原文件名命名。逐张汇报裁剪前后行列数，失败的单独列出。相比手工在 ArcToolbox 里一张张点，适合分幅影像或多年份影像的批量切边。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 影像按范围批量裁剪 or similar operations.
description_en: 用一个矢量范围（如村界、项目红线）批量裁剪一批影像/DEM，输出按原文件名命名。逐张汇报裁剪前后行列数，失败的单独列出。相比手工在 ArcToolbox 里一张张点，适合分幅影像或多年份影像的批量切边。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 影像按范围批量裁剪 or similar operations.
description_zh: 用一个矢量范围（如村界、项目红线）批量裁剪一批影像/DEM，输出按原文件名命名。逐张汇报裁剪前后行列数，失败的单独列出。相比手工在 ArcToolbox 里一张张点，适合分幅影像或多年份影像的批量切边。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「影像按范围批量裁剪」或同类操作时使用。
argument-hint: <输入栅格（多个，用分号分隔）> <裁剪范围（要素类）> <输出文件夹或工作空间>
argument-hint-en: <输入栅格（多个，用分号分隔）> <裁剪范围（要素类）> <输出文件夹或工作空间>
argument-hint-zh: <输入栅格（多个，用分号分隔）> <裁剪范围（要素类）> <输出文件夹或工作空间>
user-invocable: true
---

# 影像按范围批量裁剪

## 功能
用一个矢量范围（如村界、项目红线）批量裁剪一批影像/DEM，输出按原文件名命名。逐张汇报裁剪前后行列数，失败的单独列出。相比手工在 ArcToolbox 里一张张点，适合分幅影像或多年份影像的批量切边。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入栅格（多个，用分号分隔）
- 裁剪范围（要素类）
- 输出文件夹或工作空间
- 输出位置（GDB 要素类 / csv 路径）
- 坐标系要求：涉及面积时必须确认是否为投影坐标系（脚本已自动按坐标系切换测地面积）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 读回输出图层行数/字段值或打开结果表抽查 3 项与预期一致；
- 报出的「待人工细分」「问题清单」必须原样反馈给用户，不要自行取舍。

## 参数与调用
```bat
python scripts\run.py <输入栅格（多个，用分号分隔）> <裁剪范围（要素类）> <输出文件夹或工作空间>
```

## 来源
来自公开开源工具箱的业务口径整理，已去除原作者与界面可见信息；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
