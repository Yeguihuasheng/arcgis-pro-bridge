---
name: tool-file-to-blob
name_en: 文件写入 BLOB 字段
name_zh: 文件写入 BLOB 字段
description: 通过表连接把文件名与要素 ID 关联，再把对应文件读入要素类的 BLOB 字段，完成后清理连接字段，用于把外业照片回挂到要素上。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 文件写入 BLOB 字段 or similar operations.
description_en: 通过表连接把文件名与要素 ID 关联，再把对应文件读入要素类的 BLOB 字段，完成后清理连接字段，用于把外业照片回挂到要素上。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 文件写入 BLOB 字段 or similar operations.
description_zh: 通过表连接把文件名与要素 ID 关联，再把对应文件读入要素类的 BLOB 字段，完成后清理连接字段，用于把外业照片回挂到要素上。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「文件写入 BLOB 字段」或同类操作时使用。
argument-hint: <目标要素类> <要素类中的关联字段> <连接表> <连接表的关联字段> <连接表中存放文件名的字段> <待写入文件所在文件夹> <要写入的 BLOB 字段名>
argument-hint-en: <目标要素类> <要素类中的关联字段> <连接表> <连接表的关联字段> <连接表中存放文件名的字段> <待写入文件所在文件夹> <要写入的 BLOB 字段名>
argument-hint-zh: <目标要素类> <要素类中的关联字段> <连接表> <连接表的关联字段> <连接表中存放文件名的字段> <待写入文件所在文件夹> <要写入的 BLOB 字段名>
user-invocable: true
---

# 文件写入 BLOB 字段

## 功能
通过表连接把文件名与要素 ID 关联，再把对应文件读入要素类的 BLOB 字段，完成后清理连接字段，用于把外业照片回挂到要素上。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 目标要素类
- 要素类中的关联字段
- 连接表
- 连接表的关联字段
- 连接表中存放文件名的字段
- 待写入文件所在文件夹
- 要写入的 BLOB 字段名
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 目标要素类（原参数名：outFeatureClass）
2. 要素类中的关联字段（原参数名：in_field）
3. 连接表（原参数名：join_table）
4. 连接表的关联字段（原参数名：join_field）
5. 连接表中存放文件名的字段（原参数名：inFieldName）
6. 待写入文件所在文件夹（原参数名：inFolder）
7. 要写入的 BLOB 字段名（原参数名：outFieldName）

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
python scripts\run.py <目标要素类> <要素类中的关联字段> <连接表> <连接表的关联字段> <连接表中存放文件名的字段> <待写入文件所在文件夹> <要写入的 BLOB 字段名>
```
参数说明：

1. 目标要素类（原参数名：outFeatureClass）
2. 要素类中的关联字段（原参数名：in_field）
3. 连接表（原参数名：join_table）
4. 连接表的关联字段（原参数名：join_field）
5. 连接表中存放文件名的字段（原参数名：inFieldName）
6. 待写入文件所在文件夹（原参数名：inFolder）
7. 要写入的 BLOB 字段名（原参数名：outFieldName）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
