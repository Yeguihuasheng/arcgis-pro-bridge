---
name: tool-map-match
name_en: 轨迹点地图匹配
name_zh: 轨迹点地图匹配
description: 把 GPS 轨迹点匹配吸附到道路网络线上，输出匹配后的轨迹，用于外业轨迹纠偏、路径还原。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 轨迹点地图匹配 or similar operations.
description_en: 把 GPS 轨迹点匹配吸附到道路网络线上，输出匹配后的轨迹，用于外业轨迹纠偏、路径还原。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 轨迹点地图匹配 or similar operations.
description_zh: 把 GPS 轨迹点匹配吸附到道路网络线上，输出匹配后的轨迹，用于外业轨迹纠偏、路径还原。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「轨迹点地图匹配」或同类操作时使用。
argument-hint: <输入轨迹点（shp）> <输入道路网（shp）> <网络距离衰减常数（米）> <欧氏距离衰减常数（米）> <候选路段的最大欧氏距离（米）> <输出要素>
argument-hint-en: <输入轨迹点（shp）> <输入道路网（shp）> <网络距离衰减常数（米）> <欧氏距离衰减常数（米）> <候选路段的最大欧氏距离（米）> <输出要素>
argument-hint-zh: <输入轨迹点（shp）> <输入道路网（shp）> <网络距离衰减常数（米）> <欧氏距离衰减常数（米）> <候选路段的最大欧氏距离（米）> <输出要素>
user-invocable: true
---

# 轨迹点地图匹配

## 功能
把 GPS 轨迹点匹配吸附到道路网络线上，输出匹配后的轨迹，用于外业轨迹纠偏、路径还原。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入轨迹点（shp）
- 输入道路网（shp）
- 网络距离衰减常数（米）
- 欧氏距离衰减常数（米）
- 候选路段的最大欧氏距离（米）
- 输出要素
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入轨迹点（shp）（原参数名：Input track (shp)）
2. 输入道路网（shp）（原参数名：Input road network (shp)）
3. 网络距离衰减常数（米）（原参数名：Decay constant on network (in meter)）
4. 欧氏距离衰减常数（米）（原参数名：Decay constant for Eucl. distances (in meter)）
5. 候选路段的最大欧氏距离（米）（原参数名：maximum Eucl. distance for selecting segment candidates (in meter)）
6. 输出要素（原参数名：Output Features）

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
python scripts\run.py <输入轨迹点（shp）> <输入道路网（shp）> <网络距离衰减常数（米）> <欧氏距离衰减常数（米）> <候选路段的最大欧氏距离（米）> <输出要素>
```
参数说明：

1. 输入轨迹点（shp）（原参数名：Input track (shp)）
2. 输入道路网（shp）（原参数名：Input road network (shp)）
3. 网络距离衰减常数（米）（原参数名：Decay constant on network (in meter)）
4. 欧氏距离衰减常数（米）（原参数名：Decay constant for Eucl. distances (in meter)）
5. 候选路段的最大欧氏距离（米）（原参数名：maximum Eucl. distance for selecting segment candidates (in meter)）
6. 输出要素（原参数名：Output Features）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
