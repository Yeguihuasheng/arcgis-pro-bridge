---
name: geom-spatial-angle-join
name_en: 按夹角最近空间连接线
name_zh: 按夹角最近空间连接线
description: 在搜索半径内为目标线找方向夹角最接近的连接线并做一对一空间连接，用于路网接驳、等高线接边、管线顺接。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按夹角最近空间连接线 or similar operations.
description_en: 在搜索半径内为目标线找方向夹角最接近的连接线并做一对一空间连接，用于路网接驳、等高线接边、管线顺接。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按夹角最近空间连接线 or similar operations.
description_zh: 在搜索半径内为目标线找方向夹角最接近的连接线并做一对一空间连接，用于路网接驳、等高线接边、管线顺接。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「按夹角最近空间连接线」或同类操作时使用。
argument-hint: <目标线要素> <连接线要素> <输入工作空间> <输出线要素> <搜索半径> <是否覆盖输出>
argument-hint-en: <目标线要素> <连接线要素> <输入工作空间> <输出线要素> <搜索半径> <是否覆盖输出>
argument-hint-zh: <目标线要素> <连接线要素> <输入工作空间> <输出线要素> <搜索半径> <是否覆盖输出>
user-invocable: true
---

# 按夹角最近空间连接线

## 功能
在搜索半径内为目标线找方向夹角最接近的连接线并做一对一空间连接，用于路网接驳、等高线接边、管线顺接。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 目标线要素
- 连接线要素
- 输入工作空间
- 输出线要素
- 搜索半径
- 是否覆盖输出
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 目标线要素（原参数名：Target Lines）
2. 连接线要素（原参数名：Join Lines）
3. 输入工作空间（原参数名：Workspace）
4. 输出线要素（原参数名：Output Lines）
5. 搜索半径（原参数名：Search Radius）
6. 是否覆盖输出（原参数名：Overwrite Output）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按上表顺序传入）。
运行环境：ArcGIS Pro

## 执行后复核
- 读回输出的行数/字段值或打开结果文件抽查 3 项；
- 报错时看 traceback 定位到具体参数。

## 详细说明
需要 numpy；一对一匹配，只在搜索半径内且角度差最小的线才会连上。

## 参数与调用
```bat
python scripts\run.py <目标线要素> <连接线要素> <输入工作空间> <输出线要素> <搜索半径> <是否覆盖输出>
```
参数说明：

1. 目标线要素（原参数名：Target Lines）
2. 连接线要素（原参数名：Join Lines）
3. 输入工作空间（原参数名：Workspace）
4. 输出线要素（原参数名：Output Lines）
5. 搜索半径（原参数名：Search Radius）
6. 是否覆盖输出（原参数名：Overwrite Output）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
