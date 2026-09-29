---
name: plan-code-check
name_en: 地类编码与名称一致性检查
name_zh: 地类编码与名称一致性检查
description: 逐图斑核对用地代码与名称是否匹配（按用地用海对照表），检出缺码、错码、新旧标准混用、代码与名称不符等问题，输出问题清单 CSV。对应原工具箱的「地类编号名称别称匹配检查 / 检查地块编号和土地码是否有问题」。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 地类编码与名称一致性检查 or similar operations.
description_en: 逐图斑核对用地代码与名称是否匹配（按用地用海对照表），检出缺码、错码、新旧标准混用、代码与名称不符等问题，输出问题清单 CSV。对应原工具箱的「地类编号名称别称匹配检查 / 检查地块编号和土地码是否有问题」。 Runs inside ArcGIS Pro via the YghsBridge MCP channel. Use when the user asks for 地类编码与名称一致性检查 or similar operations.
description_zh: 逐图斑核对用地代码与名称是否匹配（按用地用海对照表），检出缺码、错码、新旧标准混用、代码与名称不符等问题，输出问题清单 CSV。对应原工具箱的「地类编号名称别称匹配检查 / 检查地块编号和土地码是否有问题」。 经 YghsBridge MCP 在 ArcGIS Pro 内执行；用户提到「地类编码与名称一致性检查」或同类操作时使用。
argument-hint: <用地图层> <用地代码字段（默认 YDYHFLDM）> <用地名称字段（默认 YDYHFLMC）> <输出问题清单 CSV>
argument-hint-en: <用地图层> <用地代码字段（默认 YDYHFLDM）> <用地名称字段（默认 YDYHFLMC）> <输出问题清单 CSV>
argument-hint-zh: <用地图层> <用地代码字段（默认 YDYHFLDM）> <用地名称字段（默认 YDYHFLMC）> <输出问题清单 CSV>
user-invocable: true
---

# 地类编码与名称一致性检查

## 功能
逐图斑核对用地代码与名称是否匹配（按用地用海对照表），检出缺码、错码、新旧标准混用、代码与名称不符等问题，输出问题清单 CSV。对应原工具箱的「地类编号名称别称匹配检查 / 检查地块编号和土地码是否有问题」。

## 使用前必须先问询（缺一不可）
用 AskUserQuestion 逐项确认下列参数，全部明确后才执行；不确定的给候选值让用户选：
- 用地图层
- 用地代码字段（默认 YDYHFLDM）
- 用地名称字段（默认 YDYHFLMC）
- 输出问题清单 CSV
- 输出位置（GDB 要素类 / csv 路径）
- 坐标系要求：涉及面积时必须确认是否为投影坐标系（脚本已自动按坐标系切换测地面积）

## 执行路径
直接执行本技能的 `scripts/run.py`（参数按顺序传入）。运行环境：ArcGIS Pro

## 执行后复核
- 读回输出图层行数/字段值或打开结果表抽查 3 项与预期一致；
- 报出的「待人工细分」「问题清单」必须原样反馈给用户，不要自行取舍。

## 参数与调用
```bat
python scripts\run.py <用地图层> <用地代码字段（默认 YDYHFLDM）> <用地名称字段（默认 YDYHFLMC）> <输出问题清单 CSV>
```

## 来源
来自公开开源工具箱的业务口径整理，已去除原作者与界面可见信息；
原始出处与许可证见仓库根目录 `ATTRIBUTION.md`。
