# -*- coding: utf-8 -*-
"""
坐标半径表转圆面 —— ArcGIS Pro 版

按表中的圆心坐标与半径字段生成圆形面要素，用于设施影响圈、信号覆盖示意。

参数顺序（按地理处理工具原定义）：
  1. In Records（In Records）
  2. SpatialReference（SpatialReference）
  3. CenterX（CenterX）
  4. CenterY（CenterY）
  5. radius（radius）
  6. Output Features（Output Features）

用法：
    python run.py <In Records> <SpatialReference> <CenterX> <CenterY> <radius> <Output Features>
"""
# -*- coding: UTF-8 -*-

import sys
import arcpy


# ---- 生成器补充的运行期兜底（不影响原逻辑）----
# 上游脚本的中间结果常放在 in_memory，重复运行会因为重名而失败，
# 打开覆盖输出后再跑就正常了。
try:
    arcpy.env.overwriteOutput = True
except Exception:
    pass
# 上游的错误处理分支里偶有引用未定义的变量（如 out_fc_name / out_ws），
# 一旦走到那里会抛 NameError 把真正的错误掩盖掉，这里给这些名字兜底。
for _n in ("out_fc_name", "out_ws", "out_fc", "fc_name", "out_name"):
    if _n not in globals():
        globals()[_n] = u""
del _n


import os
import codecs
import datetime
#import pytz

#ツール定義

class TableToCircle(object):

  def __init__(self):
    self.label = "Table To Circle"
    self.description = "Creates a circular  polygon from a table."

    self.category = "DataManagement"
    self.canRunInBackground = False

  def getParameterInfo(self):

    param0 = arcpy.Parameter(
               displayName="In Records",
               name="in_layer",
               datatype=["GPTableView", "DETable"],
               parameterType="Required",
               direction="Input")

    param1 = arcpy.Parameter(
               displayName="SpatialReference",
               name="spref",
               datatype="GPSpatialReference",
               parameterType="Required",
               direction="Input")

    param2 = arcpy.Parameter(
        displayName="CenterX",
        name="CenterX",
        datatype="Field",
        parameterType="Required",
        direction="Input")
    param2.filter.list = ['Short', 'Long', 'Double', 'Single']
    param2.parameterDependencies = [param0.name]

    param3 = arcpy.Parameter(
        displayName="CenterY",
        name="CenterY",
        datatype="Field",
        parameterType="Required",
        direction="Input")
    param3.filter.list = ['Short', 'Long', 'Double', 'Single']
    param3.parameterDependencies = [param0.name]

    param4 = arcpy.Parameter(
        displayName="radius",
        name="radius",
        datatype="Field",
        parameterType="Required",
        direction="Input")
    param4.filter.list = ['Short', 'Long', 'Double', 'Single']
    param4.parameterDependencies = [param0.name]

    param5 = arcpy.Parameter(
        displayName="Output Features",
        name="out_features",
        datatype="DEFeatureClass",
        parameterType="Required",
        #parameterType="Derived",
        direction="Output")

    params = [param0, param1, param2, param3, param4, param5]
    return params

  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    return

  def updateMessages(self, parameters):
    return

  def execute(self, parameters, messages):

    records = parameters[0].valueAsText
    spRef = parameters[1].value
    cxField = parameters[2].valueAsText
    cyField = parameters[3].valueAsText
    rField = parameters[4].valueAsText

    outFeatures = parameters[5].valueAsText
    dirName, fcName = os.path.split(outFeatures)

    arcpy.CreateFeatureclass_management(dirName, fcName, "POLYGON", None, "DISABLED", "DISABLED", spRef)
    arcpy.AddField_management(outFeatures, "LINK_ID", "LONG")

    with arcpy.da.SearchCursor(records, [cxField, cyField, rField, 'OID@']) as cursor:
      with arcpy.da.InsertCursor(outFeatures, ["LINK_ID", "SHAPE@"]) as inCursor:
        for row in cursor:
          pnt = arcpy.Point(row[0], row[1])
          pnt_geometry = arcpy.PointGeometry(pnt, spRef)

          buffered = None
          if (row[2] != 0):
            buffered = pnt_geometry.buffer(row[2])

          insertRow = (row[3], buffered)
          inCursor.insertRow(insertRow)


# ------------------------------------------------------------------ 运行入口
class _Param(object):
    """模拟地理处理参数对象（供被抽取的 execute() 使用）。"""

    def __init__(self, value):
        self.value = value
        self.valueAsText = value
        self.valueAsMultiValue = value if isinstance(value, list) else [value]
        self.altered = True

    def __str__(self):
        return str(self.value)


class _Msgs(object):
    """模拟地理处理消息对象：把 addMessage 系列接到 stdout。"""

    def addMessage(self, text):
        print(text)

    AddMessage = addMessage

    def addWarning(self, text):
        sys.stderr.write("WARN: %s\n" % text)

    AddWarning = addWarning

    def addErrorMessage(self, text):
        sys.stderr.write("ERROR: %s\n" % text)

    AddErrorMessage = addErrorMessage

    def addError(self, *a, **k):
        pass

    AddError = addError


if sys.version_info[0] >= 3:
    # 抽取的原实现常按 py2 习惯用 open(path, "wb") 写 csv，py3 下会报
    # "a bytes-like object is required"。这里只在本模块内兜一层：
    # 去掉 b、补 newline/encoding，让 csv 走文本模式。
    # 注意：只覆盖本模块全局，不影响 arcpy 内部的 open。
    _py_open = open

    def open(file, mode="r", *args, **kwargs):  # noqa: A001
        if "b" in mode:
            mode = mode.replace("b", "")
            kwargs.setdefault("newline", "")
            kwargs.setdefault("encoding", "utf-8")
        return _py_open(file, mode, *args, **kwargs)


def _to_unicode(s):
    """py2 下 sys.argv 是字节串，中文参数不解码会和 u"" 比较炸，入口统一转 unicode。"""
    if not isinstance(s, bytes):
        return s
    for enc in (u"mbcs", u"utf-8", u"gbk", u"latin-1"):
        try:
            return s.decode(enc)
        except Exception:
            continue
    return s.decode(u"utf-8", u"replace")


def _run(argv):
    if sys.version_info[0] < 3:
        argv = [_to_unicode(v) for v in argv]
    params = [_Param(v) for v in argv]
    tools = TableToCircle()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
