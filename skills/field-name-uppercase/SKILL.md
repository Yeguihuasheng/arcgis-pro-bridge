---
name: field-name-uppercase
name_en: 字段名转大写
name_zh: 字段名转大写
description: 把要素类/表的所有字段名统一改为大写，满足部分地方入库标准的命名要求。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 字段名转大写 or similar operations.
description_en: 把要素类/表的所有字段名统一改为大写，满足部分地方入库标准的命名要求。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 字段名转大写 or similar operations.
description_zh: 把要素类/表的所有字段名统一改为大写，满足部分地方入库标准的命名要求。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「字段名转大写」或同类操作时使用。
argument-hint: <输入表> <输出位置（工作空间或文件夹）> <输出表名>
argument-hint-en: <输入表> <输出位置（工作空间或文件夹）> <输出表名>
argument-hint-zh: <输入表> <输出位置（工作空间或文件夹）> <输出表名>
user-invocable: true
---

# 字段名转大写

## 功能
把要素类/表的所有字段名统一改为大写，满足部分地方入库标准的命名要求。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入表
- 输出位置（工作空间或文件夹）
- 输出表名
- 输出位置（GDB 要素类 / 表 / csv 路径）
- 坐标系要求：沿用当前工程

**原工具参数项**（提取自开源实现，作问询参照）：
1. 输入表（原工具参数名：Input Table）
2. 输出位置（工作空间或文件夹）（原工具参数名：Output Location）
3. 输出表名（原工具参数名：Output Table Name）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按上表顺序传入）。
运行环境：ArcGIS Pro

## 执行后复核
- 读回输出的行数/字段值或打开结果文件抽查 3 项；
- 报错时看 traceback 定位到具体参数。

## 详细说明
本技能抽取自社区开源工具箱的单个工具类，逻辑与参数保持原实现。

## 参数与调用
```bat
python scripts\run.py <输入表> <输出位置（工作空间或文件夹）> <输出表名>
```
参数说明：
1. 输入表（原工具参数名：Input Table）
2. 输出位置（工作空间或文件夹）（原工具参数名：Output Location）
3. 输出表名（原工具参数名：Output Table Name）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
