---
name: raster-batch-project-folder
name_en: 栅格文件夹批量投影
name_zh: 栅格文件夹批量投影
description: 把文件夹内所有栅格批量投影到指定坐标系，输出到新文件夹。用于一批影像/栅格统一坐标系（如统一投到 Web Mercator 或 CGCS2000 高斯投影），替换逐张手动投影。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_en: 把文件夹内所有栅格批量投影到指定坐标系，输出到新文件夹。用于一批影像/栅格统一坐标系（如统一投到 Web Mercator 或 CGCS2000 高斯投影），替换逐张手动投影。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_zh: 把文件夹内所有栅格批量投影到指定坐标系，输出到新文件夹。用于一批影像/栅格统一坐标系（如统一投到 Web Mercator 或 CGCS2000 高斯投影），替换逐张手动投影。经 YghsBridge MCP 在 ArcGIS Pro 内执行。
argument-hint: <输入文件夹（含栅格）> <输出文件夹> <目标坐标系（名称/WKT/.prj）> [重采样方式 默认NEAREST] [地理变换 可空]
argument-hint-en: <输入文件夹（含栅格）> <输出文件夹> <目标坐标系（名称/WKT/.prj）> [重采样方式 默认NEAREST] [地理变换 可空]
argument-hint-zh: <输入文件夹（含栅格）> <输出文件夹> <目标坐标系（名称/WKT/.prj）> [重采样方式 默认NEAREST] [地理变换 可空]
user-invocable: true
---

# 栅格文件夹批量投影

## 功能
把文件夹内所有栅格批量投影到指定坐标系，输出到新文件夹。适合一批影像/栅格统一坐标系（如统一投到 Web Mercator、CGCS2000 高斯投影），避免逐张手动投影。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入文件夹（含栅格）
- 输出文件夹（不存在会自动创建）
- 目标坐标系（坐标系名称、WKT 字符串或 .prj 文件路径）
- 重采样方式（NEAREST / BILINEAR / CUBIC，默认 NEAREST）
- 地理变换（跨基准面时填，如 ETRS_1989_To_WGS_1984，无则留空）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 抽查输出文件夹栅格数量与输入一致；
- 打开 1 张结果栅格，核对坐标系与目标一致、范围无异常。

## 参数与调用
```bat
python scripts\run.py <输入文件夹> <输出文件夹> <目标坐标系> [重采样方式] [地理变换]
```

## 来源
来自 Apache-2.0 许可的开源脚本工具（Project_Raster_Folder）的业务口径整理，已泛化为
任意目标坐标系/重采样/地理变换的通用批量投影；原始出处与许可证见 `ATTRIBUTION.md`。
