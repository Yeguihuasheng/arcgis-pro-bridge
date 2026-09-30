---
name: raster-1bit-to-8bit-png
name_en: 1bit TIFF 批量转 8bit PNG
name_zh: 1bit TIFF 批量转 8bit PNG
description: 把文件夹内所有 1bit 二值 TIFF 栅格批量转换为 8bit PNG（OneBitTo8Bit），输出到指定文件夹。用于黑白扫描图、二值掩膜、单色影像的规范化转换。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_en: 把文件夹内所有 1bit 二值 TIFF 栅格批量转换为 8bit PNG（OneBitTo8Bit），输出到指定文件夹。用于黑白扫描图、二值掩膜、单色影像的规范化转换。 Runs inside ArcGIS Pro via the YghsBridge MCP channel.
description_zh: 把文件夹内所有 1bit 二值 TIFF 栅格批量转换为 8bit PNG（OneBitTo8Bit），输出到指定文件夹。用于黑白扫描图、二值掩膜、单色影像的规范化转换。经 YghsBridge MCP 在 ArcGIS Pro 内执行。
argument-hint: <输入文件夹（含 1bit TIF）> <输出文件夹（存 PNG）>
argument-hint-en: <输入文件夹（含 1bit TIF）> <输出文件夹（存 PNG）>
argument-hint-zh: <输入文件夹（含 1bit TIF）> <输出文件夹（存 PNG）>
user-invocable: true
---

# 1bit TIFF 批量转 8bit PNG

## 功能
把文件夹内所有 1bit 二值 TIFF 栅格批量转换为 8bit PNG，输出到指定文件夹。适用于黑白扫描图、二值掩膜、单色影像等需要把 1bit 转成可常规显示/处理的 8bit 栅格。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入文件夹（含 1bit TIF 栅格）
- 输出文件夹（PNG 存放处，不存在会自动创建）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 抽查输出文件夹里 PNG 数量与输入 TIF 数量一致；
- 打开 1 张 PNG 确认由黑白二值转成了正常灰度/彩色显示。

## 参数与调用
```bat
python scripts\run.py <输入文件夹> <输出文件夹>
```

## 来源
来自 Apache-2.0 许可的开源脚本工具（Convert_1bit_Tiffs_to8bit_Png）的业务口径整理；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
