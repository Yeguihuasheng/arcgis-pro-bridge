---
name: gdb-truncate-data
name_zh: 清空GDB要素数据
description_zh: 批量清空地理数据库（GDB）内要素数据集下所有要素类的数据，保留表结构。⚠️ 破坏性操作，执行前必须逐项确认。经 YghsBridge MCP 在 ArcGIS Pro 内执行。
argument-hint-zh: 需要：GDB 路径；是否含数据集外的独立要素类；是否已确认无需备份
user-invocable: true
---

# 清空GDB要素数据

## 功能

遍历指定 GDB 中**所有要素数据集**下的所有要素类，用 `TruncateTable` 把表中数据全部清空，
**保留字段结构与坐标系定义**（与 DeleteRows 相比更快且重置 OID）。
适用于：入库前清空模板库、重置测试库、批量初始化成果库。

## ⚠️ 破坏性操作

本技能**不可逆地删除数据**。执行前必须确认：
- GDB 路径准确无误（错一个字符可能清掉别的库）
- 数据确实不再需要，或已有备份

## 使用前必须先问询

- **GDB 路径**（完整路径，AI 应复述一遍让用户确认）
- **范围确认**：原版工具**只清「要素数据集内」的要素类**，数据集外的独立要素类默认**不清**——
  是否需要扩展为"同时清空独立要素类"？（问询时必须向用户说明这一差异）
- **备份确认**：是否已有备份 / 是否需要先把数据导出留档
- **排除项**：是否有个别要素类要跳过不清

## 原窗体参数项

- 输入 GDB 路径（原版为唯一参数 input_gdb）

## 执行方式

桥等效实现（与原版算法一致，经 MCP `run_python` 在 Pro 内执行）：

```python
import arcpy
arcpy.env.workspace = input_gdb
for ds in arcpy.ListDatasets(feature_type="Feature") or []:
    for fc in arcpy.ListFeatureClasses("", "All", ds) or []:
        arcpy.management.TruncateTable(fc)   # 清空数据，保留结构
        print("Cleared all data in feature class: " + fc)
```

可选扩展（用户确认后追加）：

```python
# 同时清空数据集外的独立要素类（原版不含此步）
for fc in arcpy.ListFeatureClasses() or []:
    arcpy.management.TruncateTable(fc)
```

注意：
- `TruncateTable` 不支持 Shapefile 与查询图层；遇到会报错，应跳过并提示
- 数据被锁定（编辑会话/其他进程占用）时会失败——先让用户关闭相关会话

## 执行后复核

- 逐个 GetCount 确认要素数为 0，向用户汇报"清空 N 个要素类"
- 字段数与清空前一致（结构未损）
- 把清空清单（要素类名）完整列给用户

## 详细说明

**源码**：完整随附于本技能目录——`source/original_tool.py`（原始工具箱脚本，逐字保留）。

**与原版的差异**：原版仅遍历要素数据集（`ListDatasets(feature_type='Feature')`）内的要素类；
独立要素类、普通表（Table）均不在处理范围。桥实现按问询结果决定是否扩展范围。
