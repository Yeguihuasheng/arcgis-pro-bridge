---
name: tool-sun-position
name_en: 太阳位置与山体阴影计算
name_zh: 太阳位置与山体阴影计算
description: 按日期时间计算太阳方位角与高度角，并可生成对应时刻的山体阴影（Hillshade），用于日照分析、建筑阴影与光伏选址的时相设定。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 太阳位置与山体阴影计算 or similar operations.
description_en: 按日期时间计算太阳方位角与高度角，并可生成对应时刻的山体阴影（Hillshade），用于日照分析、建筑阴影与光伏选址的时相设定。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 太阳位置与山体阴影计算 or similar operations.
description_zh: 按日期时间计算太阳方位角与高度角，并可生成对应时刻的山体阴影（Hillshade），用于日照分析、建筑阴影与光伏选址的时相设定。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「太阳位置与山体阴影计算」或同类操作时使用。
argument-hint: <分析范围面要素> <高程栅格> <日期时间> <时区> <输出山体阴影栅格>
argument-hint-en: <分析范围面要素> <高程栅格> <日期时间> <时区> <输出山体阴影栅格>
argument-hint-zh: <分析范围面要素> <高程栅格> <日期时间> <时区> <输出山体阴影栅格>
user-invocable: true
---

# 太阳位置与山体阴影计算

## 功能
按日期时间计算太阳方位角与高度角，并可生成对应时刻的山体阴影（Hillshade），用于日照分析、建筑阴影与光伏选址的时相设定。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 分析范围面要素
- 高程栅格
- 日期时间
- 时区
- 输出山体阴影栅格
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 分析范围面要素（原参数名：inputAOI）
2. 高程栅格（原参数名：inputElevation）
3. 日期时间（原参数名：inputDatetime）
4. 时区（原参数名：inputTimezone）
5. 输出山体阴影栅格（原参数名：outputHillshade）

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
python scripts\run.py <分析范围面要素> <高程栅格> <日期时间> <时区> <输出山体阴影栅格>
```
参数说明：

1. 分析范围面要素（原参数名：inputAOI）
2. 高程栅格（原参数名：inputElevation）
3. 日期时间（原参数名：inputDatetime）
4. 时区（原参数名：inputTimezone）
5. 输出山体阴影栅格（原参数名：outputHillshade）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
