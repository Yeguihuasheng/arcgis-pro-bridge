---
name: hydro-hydrodem
name_en: 水文 DEM 生成（河槽烧录）
name_zh: 水文 DEM 生成（河槽烧录）
description: 把裁切线（cutlines）按指定栅格宽度下切烧录进 DEM，得到「水文修正 DEM」，使后续流向与河网提取能沿真实河道走。需要 Spatial Analyst 许可。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 水文 DEM 生成（河槽烧录） or similar operations.
description_en: 把裁切线（cutlines）按指定栅格宽度下切烧录进 DEM，得到「水文修正 DEM」，使后续流向与河网提取能沿真实河道走。需要 Spatial Analyst 许可。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 水文 DEM 生成（河槽烧录） or similar operations.
description_zh: 把裁切线（cutlines）按指定栅格宽度下切烧录进 DEM，得到「水文修正 DEM」，使后续流向与河网提取能沿真实河道走。需要 Spatial Analyst 许可。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「水文 DEM 生成（河槽烧录）」或同类操作时使用。
argument-hint: <输出工作空间（GDB 或文件夹）> <裁切线要素类> <输入 DEM 栅格> <下切加宽的栅格单元数>
argument-hint-en: <输出工作空间（GDB 或文件夹）> <裁切线要素类> <输入 DEM 栅格> <下切加宽的栅格单元数>
argument-hint-zh: <输出工作空间（GDB 或文件夹）> <裁切线要素类> <输入 DEM 栅格> <下切加宽的栅格单元数>
user-invocable: true
---

# 水文 DEM 生成（河槽烧录）

## 功能
把裁切线（cutlines）按指定栅格宽度下切烧录进 DEM，得到「水文修正 DEM」，使后续流向与河网提取能沿真实河道走。需要 Spatial Analyst 许可。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输出工作空间（GDB 或文件夹）
- 裁切线要素类
- 输入 DEM 栅格
- 下切加宽的栅格单元数
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输出工作空间（GDB 或文件夹）（原参数名：output_workspace）
2. 裁切线要素类（原参数名：cutlines）
3. 输入 DEM 栅格（原参数名：dem）
4. 下切加宽的栅格单元数（原参数名：widen_cells）

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
python scripts\run.py <输出工作空间（GDB 或文件夹）> <裁切线要素类> <输入 DEM 栅格> <下切加宽的栅格单元数>
```
参数说明：

1. 输出工作空间（GDB 或文件夹）（原参数名：output_workspace）
2. 裁切线要素类（原参数名：cutlines）
3. 输入 DEM 栅格（原参数名：dem）
4. 下切加宽的栅格单元数（原参数名：widen_cells）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
