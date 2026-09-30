---
name: field-set-alias-from-table
name_en: 按对照表设置字段别名
name_zh: 按对照表设置字段别名
description: 按一张「字段名-别名」对照表批量改写要素类的字段别名，用于按数据库标准批量规范字段显示名。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按对照表设置字段别名 or similar operations.
description_en: 按一张「字段名-别名」对照表批量改写要素类的字段别名，用于按数据库标准批量规范字段显示名。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按对照表设置字段别名 or similar operations.
description_zh: 按一张「字段名-别名」对照表批量改写要素类的字段别名，用于按数据库标准批量规范字段显示名。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「按对照表设置字段别名」或同类操作时使用。
argument-hint: <输入表> <Output Table> <字段对照表> <存放字段名的字段> <存放别名的字段>
argument-hint-en: <输入表> <Output Table> <字段对照表> <存放字段名的字段> <存放别名的字段>
argument-hint-zh: <输入表> <Output Table> <字段对照表> <存放字段名的字段> <存放别名的字段>
user-invocable: true
---

# 按对照表设置字段别名

## 功能
按一张「字段名-别名」对照表批量改写要素类的字段别名，用于按数据库标准批量规范字段显示名。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入表
- Output Table
- 字段对照表
- 存放字段名的字段
- 存放别名的字段
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入表（原参数名：Input Table）
2. Output Table（原参数名：Output Table）
3. 字段对照表（原参数名：FieldInfo Table）
4. 存放字段名的字段（原参数名：FieldNameField）
5. 存放别名的字段（原参数名：FieldAliasField）

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
python scripts\run.py <输入表> <Output Table> <字段对照表> <存放字段名的字段> <存放别名的字段>
```
参数说明：

1. 输入表（原参数名：Input Table）
2. Output Table（原参数名：Output Table）
3. 字段对照表（原参数名：FieldInfo Table）
4. 存放字段名的字段（原参数名：FieldNameField）
5. 存放别名的字段（原参数名：FieldAliasField）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
