---
name: field-update-by-layer
name_en: 按另一图层更新字段
name_zh: 按另一图层更新字段
description: 用另一图层的同名字段回写当前图层（等价于「挂接+字段计算」但不落地中间结果），适合属性批量赋值。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按另一图层更新字段 or similar operations.
description_en: 用另一图层的同名字段回写当前图层（等价于「挂接+字段计算」但不落地中间结果），适合属性批量赋值。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 按另一图层更新字段 or similar operations.
description_zh: 用另一图层的同名字段回写当前图层（等价于「挂接+字段计算」但不落地中间结果），适合属性批量赋值。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「按另一图层更新字段」或同类操作时使用。
argument-hint: <输入数据集（要素类或 shapefile）> <输入图层的连接字段> <需要被更新的字段> <连接表> <连接表的字段> <连接表的参考字段>
argument-hint-en: <输入数据集（要素类或 shapefile）> <输入图层的连接字段> <需要被更新的字段> <连接表> <连接表的字段> <连接表的参考字段>
argument-hint-zh: <输入数据集（要素类或 shapefile）> <输入图层的连接字段> <需要被更新的字段> <连接表> <连接表的字段> <连接表的参考字段>
user-invocable: true
---

# 按另一图层更新字段

## 功能
用另一图层的同名字段回写当前图层（等价于「挂接+字段计算」但不落地中间结果），适合属性批量赋值。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入数据集（要素类或 shapefile）
- 输入图层的连接字段
- 需要被更新的字段
- 连接表
- 连接表的字段
- 连接表的参考字段
- 输出位置（GDB 要素类 / 表 / csv 路径）
- 坐标系要求：沿用当前工程

**原工具参数项**（提取自开源实现，作问询参照）：
1. 输入数据集（要素类或 shapefile）（原工具参数名：Input Dataset (feature class or shapefile)）
2. 输入图层的连接字段（原工具参数名：Input Join Field）
3. 需要被更新的字段（原工具参数名：Input Update Field）
4. 连接表（原工具参数名：Join Table）
5. 连接表的字段（原工具参数名：Join Table Field）
6. 连接表的参考字段（原工具参数名：Join Reference Field）

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
python scripts\run.py <输入数据集（要素类或 shapefile）> <输入图层的连接字段> <需要被更新的字段> <连接表> <连接表的字段> <连接表的参考字段>
```
参数说明：
1. 输入数据集（要素类或 shapefile）（原工具参数名：Input Dataset (feature class or shapefile)）
2. 输入图层的连接字段（原工具参数名：Input Join Field）
3. 需要被更新的字段（原工具参数名：Input Update Field）
4. 连接表（原工具参数名：Join Table）
5. 连接表的字段（原工具参数名：Join Table Field）
6. 连接表的参考字段（原工具参数名：Join Reference Field）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
