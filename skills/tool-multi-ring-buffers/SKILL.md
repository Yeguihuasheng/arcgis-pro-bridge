---
name: tool-multi-ring-buffers
name_en: 多环缓冲（含负缓冲）
name_zh: 多环缓冲（含负缓冲）
description: 按一组逗号分隔的距离（支持负值=向内）生成多环缓冲，并把缓冲距离写进属性字段后合并成一个面要素类；适合做由近及远的圈层分析。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 多环缓冲（含负缓冲） or similar operations.
description_en: 按一组逗号分隔的距离（支持负值=向内）生成多环缓冲，并把缓冲距离写进属性字段后合并成一个面要素类；适合做由近及远的圈层分析。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 多环缓冲（含负缓冲） or similar operations.
description_zh: 按一组逗号分隔的距离（支持负值=向内）生成多环缓冲，并把缓冲距离写进属性字段后合并成一个面要素类；适合做由近及远的圈层分析。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「多环缓冲（含负缓冲）」或同类操作时使用。
argument-hint: <输入要素类> <输出工作空间> <输出要素类> <缓冲距离列表（逗号分隔，负值向内）> <融合字段（可多个）>
argument-hint-en: <输入要素类> <输出工作空间> <输出要素类> <缓冲距离列表（逗号分隔，负值向内）> <融合字段（可多个）>
argument-hint-zh: <输入要素类> <输出工作空间> <输出要素类> <缓冲距离列表（逗号分隔，负值向内）> <融合字段（可多个）>
user-invocable: true
---

# 多环缓冲（含负缓冲）

## 功能
按一组逗号分隔的距离（支持负值=向内）生成多环缓冲，并把缓冲距离写进属性字段后合并成一个面要素类；适合做由近及远的圈层分析。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入要素类
- 输出工作空间
- 输出要素类
- 缓冲距离列表（逗号分隔，负值向内）
- 融合字段（可多个）
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入要素类（原参数名：in_fc）
2. 输出工作空间（原参数名：wspace）
3. 输出要素类（原参数名：out_fc）
4. 缓冲距离列表（逗号分隔，负值向内）（原参数名：distances）
5. 融合字段（可多个）（原参数名：dissolveFields）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按上表顺序传入）。
运行环境：ArcGIS Pro

## 执行后复核
- 读回输出的行数/字段值或打开结果文件抽查 3 项；
- 报错时看 traceback 定位到具体参数。

## 详细说明
第 4 个参数 distances 用逗号分隔多个缓冲距离（负数表示向内缓冲），第 5 个 dissolveFields 用逗号分隔需要保留的属性字段；本实现已按 ArcGIS Pro 把线侧参数由 OUTSIDE_ONLY 改为 FULL（Pro 的 Buffer 不接受 OUTSIDE_ONLY，否则报 ERROR 000800）。

## 参数与调用
```bat
python scripts\run.py <输入要素类> <输出工作空间> <输出要素类> <缓冲距离列表（逗号分隔，负值向内）> <融合字段（可多个）>
```
参数说明：

1. 输入要素类（原参数名：in_fc）
2. 输出工作空间（原参数名：wspace）
3. 输出要素类（原参数名：out_fc）
4. 缓冲距离列表（逗号分隔，负值向内）（原参数名：distances）
5. 融合字段（可多个）（原参数名：dissolveFields）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
