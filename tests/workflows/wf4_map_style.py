# -*- coding: utf-8 -*-
"""WF4 复杂流程：地图与符号化（arcpy.mp 在当前工程内操作）
    新建地图 → 加入要素类 → 按「用地性质」做唯一值符号化（CIM 改颜色）→ 保存工程

⚠️ 会往当前工程里新建一个地图「WF测试_符号化」（可随时手动删除，或跑本脚本尾部提示的命令）。
前置：先跑 wf1_data_pipeline.py（提供 wf.gdb\地块 与 用地融合）
"""
import os
import time

import arcpy

ROOT = r"A:\GisProTest\_wf_test"
GDB = os.path.join(ROOT, "wf.gdb")
FC = os.path.join(GDB, u"地块")
MAP_NAME = u"WF测试_符号化"
T0 = time.time()


def step(msg):
    print(u"[%5.1fs] %s" % (time.time() - T0, msg))


if not arcpy.Exists(FC):
    raise RuntimeError(u"缺少 wf.gdb\\地块 —— 请先运行 wf1_data_pipeline.py")

proj = arcpy.mp.ArcGISProject("CURRENT")
step(u"当前工程：%s" % os.path.basename(proj.filePath))

# ---------- 1) 建图（已存在则先删）----------
for m in proj.listMaps():
    if m.name == MAP_NAME:
        proj.deleteItem(m)
        step(u"已删除同名旧地图")
m = proj.createMap(MAP_NAME)
step(u"已新建地图「%s」" % MAP_NAME)

# ---------- 2) 加图层 ----------
lyr = m.addDataFromPath(FC)
lyr.name = u"地块"
step(u"已加入图层「地块」（%d 个要素）" % int(arcpy.management.GetCount(FC)[0]))

# ---------- 3) 唯一值符号化（按用地性质给三种颜色）----------
COLORS = {
    u"居住用地": [250, 230, 160, 100],      # 浅黄
    u"商业用地": [240, 150, 120, 100],      # 珊瑚
    u"公共服务设施用地": [150, 200, 230, 100],  # 浅蓝
}


def poly_symbol(rgb):
    return {
        "type": "CIMPolygonSymbol",
        "symbolLayers": [
            {"type": "CIMSolidStroke", "enable": True, "width": 0.6,
             "color": {"type": "CIMRGBColor", "values": [120, 120, 120, 100]}},
            {"type": "CIMSolidFill", "enable": True,
             "color": {"type": "CIMRGBColor", "values": rgb}},
        ],
    }


classes = []
for use, rgb in COLORS.items():
    classes.append({
        "type": "CIMUniqueValueClass",
        "label": use,
        "patch": "Default",
        "symbol": poly_symbol(rgb),
        "values": [{"type": "CIMUniqueValue", "fieldValues": [use]}],
        "visible": True,
    })

cim = lyr.getDefinition("V3")
cim.renderer = {
    "type": "CIMUniqueValueRenderer",
    "fields": [u"用地性质"],
    "groups": [{"type": "CIMUniqueValueGroup", "heading": u"用地性质", "classes": classes}],
    "useDefaultSymbol": False,
    "defaultLabel": u"<其他>",
}
lyr.setDefinition(cim)
step(u"已按「用地性质」设置唯一值符号（%d 类）" % len(classes))

# ---------- 4) 标注（按地块编号）----------
try:
    cim2 = lyr.getDefinition("V3")
    cim2.labelClasses = [{
        "type": "CIMLabelClass",
        "expression": "$feature.地块编号",
        "expressionEngine": "Arcade",
        "name": u"地块编号",
        "visibility": True,
        "textSymbol": {"type": "CIMTextSymbol", "height": 8, "fontFamilyName": "Microsoft YaHei"},
        "useCodedValue": False,
    }]
    lyr.setDefinition(cim2)
    lyr.showLabels = True
    step(u"已开启标注（地块编号）")
except Exception as e:
    step(u"标注设置跳过：%s" % e)

# ---------- 5) 保存工程 ----------
proj.save()
step(u"工程已保存")

print(u"地图「%s」当前图层：%s" % (MAP_NAME, u"、".join(l.name for l in m.listLayers())))
print(u"在 Pro 里查看：视图 → 地图 → 选「%s」" % MAP_NAME)
print(u"（不需要时可在目录窗格里右键该地图删除）")
step(u"WF4 全部完成")
