---
name: zip-shapefiles
name_en: Shapefile 批量打包 ZIP
name_zh: Shapefile 批量打包 ZIP
description: 把文件夹内每个 shapefile（连同 .shx/.dbf/.prj/.cpg 等附属文件）分别打包成一个 ZIP，输出到指定文件夹；也支持直接传入单个 .shp 只打这一个。用于成果移交、上传、归档时按规范打包。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_en: 把文件夹内每个 shapefile（连同 .shx/.dbf/.prj/.cpg 等附属文件）分别打包成一个 ZIP，输出到指定文件夹；也支持直接传入单个 .shp 只打这一个。用于成果移交、上传、归档时按规范打包。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_zh: 把文件夹内每个 shapefile（连同 .shx/.dbf/.prj/.cpg 等附属文件）分别打包成一个 ZIP，输出到指定文件夹；也支持直接传入单个 .shp 只打这一个。用于成果移交、上传、归档时按规范打包。经 YghsBridge MCP 在 ArcGIS Pro 内执行。
argument-hint: <输入文件夹（含 .shp）或单个 .shp 文件> <输出文件夹（存 .zip）>
argument-hint-en: <输入文件夹（含 .shp）或单个 .shp 文件> <输出文件夹（存 .zip）>
argument-hint-zh: <输入文件夹（含 .shp）或单个 .shp 文件> <输出文件夹（存 .zip）>
user-invocable: true
---

# Shapefile 批量打包 ZIP

## 功能
把文件夹内每个 shapefile（连同 .shx/.dbf/.prj/.cpg/.sbn/.sbx/.xml 等附属文件）分别打包成一个 ZIP；也支持直接传入单个 .shp 文件只打这一个。用于成果移交、上传、归档时按规范打包，避免漏掉附属文件。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入：文件夹（含多个 .shp）或单个 .shp 文件路径
- 输出文件夹（ZIP 存放处，不存在会自动创建）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 抽查 1 个 ZIP 用解压软件打开，确认 .shp/.shx/.dbf/.prj 齐全；
- 输出 ZIP 数量与输入 .shp 数量一致。

## 参数与调用
```bat
python scripts\run.py <输入文件夹或单个.shp> <输出文件夹>
```

## 来源
来自 MIT 许可的开源脚本工具（zip-shapefiles）的业务口径整理，已封装为自包含 arcpy
工具；原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
