---
name: tool-coordsys-batch
name_en: 批量定义 / 投影坐标系
name_zh: 批量定义 / 投影坐标系
description: 对一批图层批量定义或投影坐标系。目标坐标系可以是 .prj 文件路径、EPSG/WKID 数字，也可以是坐标系名称。逐条汇报改前改后，避免建库时「看着都对、其实没投影」的坑。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 批量定义 / 投影坐标系 or similar operations.
description_en: 对一批图层批量定义或投影坐标系。目标坐标系可以是 .prj 文件路径、EPSG/WKID 数字，也可以是坐标系名称。逐条汇报改前改后，避免建库时「看着都对、其实没投影」的坑。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 批量定义 / 投影坐标系 or similar operations.
description_zh: 对一批图层批量定义或投影坐标系。目标坐标系可以是 .prj 文件路径、EPSG/WKID 数字，也可以是坐标系名称。逐条汇报改前改后，避免建库时「看着都对、其实没投影」的坑。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「批量定义 / 投影坐标系」或同类操作时使用。
argument-hint: <输入（多个图层用英文分号 ; 分隔，或填一个工作空间目录）> <目标坐标系（.prj 路径 / WKID / 名称）> <操作（定义 / 投影）> <输出位置（投影时必填，可空）>
argument-hint-en: <输入（多个图层用英文分号 ; 分隔，或填一个工作空间目录）> <目标坐标系（.prj 路径 / WKID / 名称）> <操作（定义 / 投影）> <输出位置（投影时必填，可空）>
argument-hint-zh: <输入（多个图层用英文分号 ; 分隔，或填一个工作空间目录）> <目标坐标系（.prj 路径 / WKID / 名称）> <操作（定义 / 投影）> <输出位置（投影时必填，可空）>
user-invocable: true
---

# 批量定义 / 投影坐标系

## 功能
对一批图层批量定义或投影坐标系。目标坐标系可以是 .prj 文件路径、EPSG/WKID 数字，也可以是坐标系名称。逐条汇报改前改后，避免建库时「看着都对、其实没投影」的坑。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 输入（多个图层用英文分号 ; 分隔，或填一个工作空间目录）
- 目标坐标系（.prj 路径 / WKID / 名称）
- 操作（定义 / 投影）
- 输出位置（投影时必填，可空）
- 输出位置（GDB 要素类 / csv 路径）
- 坐标系要求：涉及面积时必须确认是否为投影坐标系（脚本已自动按坐标系切换测地面积）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 读回输出图层行数/字段值或打开结果表抽查 3 项与预期一致；
- 报出的「待人工细分」「问题清单」必须原样反馈给用户，不要自行取舍。

## 参数与调用
```bat
python scripts\run.py <输入（多个图层用英文分号 ; 分隔，或填一个工作空间目录）> <目标坐标系（.prj 路径 / WKID / 名称）> <操作（定义 / 投影）> <输出位置（投影时必填，可空）>
```

## 来源
来自公开开源工具箱的业务口径整理，已去除原作者与界面可见信息；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
