---
name: tool-blob-to-file
name_en: BLOB 字段导出为文件
name_zh: BLOB 字段导出为文件
description: 读取要素类 BLOB 字段中的二进制内容（如巡查照片、附件），按记录逐条导出为本地文件，文件名可取自指定字段。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for BLOB 字段导出为文件 or similar operations.
description_en: 读取要素类 BLOB 字段中的二进制内容（如巡查照片、附件），按记录逐条导出为本地文件，文件名可取自指定字段。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for BLOB 字段导出为文件 or similar operations.
description_zh: 读取要素类 BLOB 字段中的二进制内容（如巡查照片、附件），按记录逐条导出为本地文件，文件名可取自指定字段。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「BLOB 字段导出为文件」或同类操作时使用。
argument-hint: <输入要素类（已加载图层可直接写图层名）> <存放文件名的字段> <BLOB 字段名> <导出文件扩展名（如 jpg）> <输出文件夹>
argument-hint-en: <输入要素类（已加载图层可直接写图层名）> <存放文件名的字段> <BLOB 字段名> <导出文件扩展名（如 jpg）> <输出文件夹>
argument-hint-zh: <输入要素类（已加载图层可直接写图层名）> <存放文件名的字段> <BLOB 字段名> <导出文件扩展名（如 jpg）> <输出文件夹>
user-invocable: true
---

# BLOB 字段导出为文件

## 功能
读取要素类 BLOB 字段中的二进制内容（如巡查照片、附件），按记录逐条导出为本地文件，文件名可取自指定字段。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入要素类（已加载图层可直接写图层名）
- 存放文件名的字段
- BLOB 字段名
- 导出文件扩展名（如 jpg）
- 输出文件夹
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入要素类（已加载图层可直接写图层名）（原参数名：fc）
2. 存放文件名的字段（原参数名：fileName_field）
3. BLOB 字段名（原参数名：BLOB_field）
4. 导出文件扩展名（如 jpg）（原参数名：fileType）
5. 输出文件夹（原参数名：destFolder）

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
python scripts\run.py <输入要素类（已加载图层可直接写图层名）> <存放文件名的字段> <BLOB 字段名> <导出文件扩展名（如 jpg）> <输出文件夹>
```
参数说明：

1. 输入要素类（已加载图层可直接写图层名）（原参数名：fc）
2. 存放文件名的字段（原参数名：fileName_field）
3. BLOB 字段名（原参数名：BLOB_field）
4. 导出文件扩展名（如 jpg）（原参数名：fileType）
5. 输出文件夹（原参数名：destFolder）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
