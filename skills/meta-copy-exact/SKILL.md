---
name: meta-copy-exact
name_en: 元数据精确复制（批量）
name_zh: 元数据精确复制（批量）
description: 把一个数据集的元数据原样（精确副本，不改写同步信息）复制给多个目标数据集，用于批量补齐成果元数据。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 元数据精确复制（批量） or similar operations.
description_en: 把一个数据集的元数据原样（精确副本，不改写同步信息）复制给多个目标数据集，用于批量补齐成果元数据。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 元数据精确复制（批量） or similar operations.
description_zh: 把一个数据集的元数据原样（精确副本，不改写同步信息）复制给多个目标数据集，用于批量补齐成果元数据。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「元数据精确复制（批量）」或同类操作时使用。
argument-hint: <元数据来源数据集> <输出文件夹>
argument-hint-en: <元数据来源数据集> <输出文件夹>
argument-hint-zh: <元数据来源数据集> <输出文件夹>
user-invocable: true
---

# 元数据精确复制（批量）

## 功能
把一个数据集的元数据原样（精确副本，不改写同步信息）复制给多个目标数据集，用于批量补齐成果元数据。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 元数据来源数据集
- 输出文件夹
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 元数据来源数据集（原参数名：inputMetadata）
2. 输出文件夹（原参数名：outputFolder）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按上表顺序传入）。
运行环境：ArcGIS Pro

## 执行后复核
- 读回输出的行数/字段值或打开结果文件抽查 3 项；
- 报错时看 traceback 定位到具体参数。

## 详细说明
本技能抽取自社区开源工具箱的单个工具，逻辑与参数保持原实现，仅把参数入口改为命令行传入。

## 参数与调用
```bat
python scripts\run.py <元数据来源数据集> <输出文件夹>
```
参数说明：

1. 元数据来源数据集（原参数名：inputMetadata）
2. 输出文件夹（原参数名：outputFolder）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
