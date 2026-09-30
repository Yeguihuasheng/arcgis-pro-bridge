---
name: geom-delete-overlap
name_en: 删除面重叠区域
name_zh: 删除面重叠区域
description: 把两组面要素相互重叠的部分从第一组里扣掉，输出不重叠的面，用于清理图斑压盖、双图层去重。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 删除面重叠区域 or similar operations.
description_en: 把两组面要素相互重叠的部分从第一组里扣掉，输出不重叠的面，用于清理图斑压盖、双图层去重。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 删除面重叠区域 or similar operations.
description_zh: 把两组面要素相互重叠的部分从第一组里扣掉，输出不重叠的面，用于清理图斑压盖、双图层去重。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「删除面重叠区域」或同类操作时使用。
argument-hint: <输入面要素类（被扣除方）> <参照面要素类（用于扣除重叠）> <输出面要素类>
argument-hint-en: <输入面要素类（被扣除方）> <参照面要素类（用于扣除重叠）> <输出面要素类>
argument-hint-zh: <输入面要素类（被扣除方）> <参照面要素类（用于扣除重叠）> <输出面要素类>
user-invocable: true
---

# 删除面重叠区域

## 功能
把两组面要素相互重叠的部分从第一组里扣掉，输出不重叠的面，用于清理图斑压盖、双图层去重。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：

- 输入面要素类（被扣除方）
- 参照面要素类（用于扣除重叠）
- 输出面要素类
- 输出位置（GDB 要素类 / 表 / 栅格 / 文件夹路径）
- 坐标系要求：涉及面积/长度/坡度时必须确认输入为投影坐标系

**原工具参数项**（提取自开源实现，作问询参照）：

1. 输入面要素类（被扣除方）（原参数名：in_poly_fc1）
2. 参照面要素类（用于扣除重叠）（原参数名：in_poly_fc2）
3. 输出面要素类（原参数名：out_poly_fc）

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
python scripts\run.py <输入面要素类（被扣除方）> <参照面要素类（用于扣除重叠）> <输出面要素类>
```
参数说明：

1. 输入面要素类（被扣除方）（原参数名：in_poly_fc1）
2. 参照面要素类（用于扣除重叠）（原参数名：in_poly_fc2）
3. 输出面要素类（原参数名：out_poly_fc）

## 来源
来自公开开源工具改造，去除原有名称与作者可见信息后重打包；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
