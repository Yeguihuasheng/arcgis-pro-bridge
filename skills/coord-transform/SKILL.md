---
name: coord-transform
name_en: 坐标纠偏（WGS84/GCJ-02/BD09 互转）
name_zh: 坐标纠偏（WGS84/GCJ-02/BD09 互转）
description: 把要素类（点/线/面）的几何坐标在 WGS84、GCJ-02（国测局/火星坐标）、BD09（百度）三种坐标系之间互相转换，输出新要素类。用于把高德/百度等平台采集坐标纠偏回 WGS84/CGCS2000 口径，或反向把标准坐标偏置到平台坐标系以便套图。只改平面 X/Y，Z/M 原样保留，空间参考不改变。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_en: 把要素类（点/线/面）的几何坐标在 WGS84、GCJ-02（国测局/火星坐标）、BD09（百度）三种坐标系之间互相转换，输出新要素类。用于把高德/百度等平台采集坐标纠偏回 WGS84/CGCS2000 口径，或反向把标准坐标偏置到平台坐标系以便套图。只改平面 X/Y，Z/M 原样保留，空间参考不改变。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_zh: 把要素类（点/线/面）的几何坐标在 WGS84、GCJ-02（国测局/火星坐标）、BD09（百度）三种坐标系之间互相转换，输出新要素类。用于把高德/百度等平台采集坐标纠偏回 WGS84/CGCS2000 口径，或反向把标准坐标偏置到平台坐标系以便套图。只改平面 X/Y，Z/M 原样保留，空间参考不改变。经 YghsBridge MCP 在 ArcGIS Pro 内执行。
argument-hint: <输入要素类（点/线/面）> <输出要素类> <源坐标系 WGS84/GCJ02/BD09/CGCS2000> <目标坐标系 WGS84/GCJ02/BD09/CGCS2000>
argument-hint-en: <输入要素类（点/线/面）> <输出要素类> <源坐标系 WGS84/GCJ02/BD09/CGCS2000> <目标坐标系 WGS84/GCJ02/BD09/CGCS2000>
argument-hint-zh: <输入要素类（点/线/面）> <输出要素类> <源坐标系 WGS84/GCJ02/BD09/CGCS2000> <目标坐标系 WGS84/GCJ02/BD09/CGCS2000>
user-invocable: true
---

# 坐标纠偏（WGS84 / GCJ-02 / BD09 互转）

## 功能
把要素类的几何坐标在 WGS84、GCJ-02（国测局/火星坐标）、BD09（百度）三种坐标系之间互相转换，输出新要素类。点/线/面都支持。典型场景：把高德/百度地图上采集的点「纠偏」回 WGS84 或 CGCS2000 口径入库；或反向把标准坐标偏置成平台坐标以便与互联网底图套图对比。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入要素类（点/线/面，路径或图层名）
- 输出要素类（新路径，避免覆盖已有数据）
- 源坐标系（WGS84 / GCJ02 / BD09 / CGCS2000）
- 目标坐标系（WGS84 / GCJ02 / BD09 / CGCS2000）
- 注意：CGCS2000 在本工具中按 WGS84 近似处理（两者椭球差异在米级以内，用于 Web 采集数据纠偏足够）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 抽查 1~2 个点在转换前后的坐标差（GCJ02→WGS84 在中国境内通常偏移 300~700 米量级）；
- 境外坐标（经度 <72.004 或 >137.8347、纬度 <0.8293 或 >55.8271）会被视为无需纠偏、原样返回。

## 参数与调用
```bat
python scripts\run.py <输入要素类> <输出要素类> <源坐标系> <目标坐标系>
```

## 来源
纠偏算法取自 MIT 许可的开源实现（WGS84/GCJ-02/BD09 标准互转公式），已封装为自包含 arcpy 工具；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
