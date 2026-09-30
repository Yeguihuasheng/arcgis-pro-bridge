# -*- coding: utf-8 -*-
"""
添加坐标字段 —— ArcGIS Pro 版

给点要素类新增 X/Y 坐标字段并写入坐标值，用于导出界址点坐标表、坐标核查。

参数顺序（按地理处理工具原定义）：
  1. Input Features（Input Features）
  2. Point Location（Point Location）
  3. Output Features（Output Features）

用法：
    python run.py <Input Features> <Point Location> <Output Features>
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

#ツール定義

class AddXYField(object):
  def __init__(self):
    self.label = "Add XY Field"
    self.description = "Adds a XY field to a feature layer."

    self.category = "Fields"
    self.canRunInBackground = False

  def getParameterInfo(self):
    param0 = arcpy.Parameter(
               displayName="Input Features",
               name="in_features",
               datatype="GPFeatureLayer",
               parameterType="Required",
               direction="Input")
    param0.filter.list = ["Point","Multipoint","Polyline","Polygon"]

    param1 = arcpy.Parameter(
               displayName="Point Location",
               name="point_location",
               datatype="GPString",
               parameterType="Required",
               direction="Input")

    param1.filter.type = "ValueList"
    param1.filter.list = ["POINT"]
    param1.enabled = False
    param1.value = "POINT"

    param2 = arcpy.Parameter(
        displayName="Output Features",
        name="out_features",
        datatype="GPFeatureLayer",
        parameterType="Derived",
        direction="Output")

    params = [param0, param1, param2]
    return params

  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    if parameters[0]:
      inFeatures = parameters[0].valueAsText
      if (inFeatures):
        inDesc = arcpy.Describe(inFeatures)
        if (inDesc.dataType == "FeatureLayer"):
          inDesc = inDesc.featureClass

        ptLocation = parameters[1]

        if ( (inDesc.shapeType == "Polygon" or
            inDesc.shapeType == "Multipoint") and not "CENTROID" in ptLocation.filter.list):
          ptLocation.filter.list = ["CENTROID", "LABELPOINT", "TRUECENTROID"]
          ptLocation.enabled = True
          ptLocation.value = "centroid"

        elif (inDesc.shapeType == "Polyline" and not "START" in ptLocation.filter.list):
          ptLocation.filter.list = ["START", "MID", "END"]
          ptLocation.enabled = True
          ptLocation.value = "START"

        elif (inDesc.shapeType == "Point" and not "POINT" in ptLocation.filter.list):
          ptLocation.filter.list = ["POINT"]
          ptLocation.enabled = False
          ptLocation.value = "POINT"

        parameters[1] = ptLocation

    return

  def updateMessages(self, parameters):
    inFeatures = parameters[0].valueAsText
    if (inFeatures):
      inDesc = arcpy.Describe(inFeatures)
      if (inDesc.dataType == "FeatureLayer"):
        inDesc = inDesc.featureClass
      # message clear ( check fieldname )
      parameters[0].clearMessage()
      fields = arcpy.ListFields(inFeatures)
      for field in fields:
        if (field.name.upper() == "X" or field.name.upper() == "Y"):
          parameters[0].setWarningMessage("The value of the [X/Y] field will be overwritten.")
          break


    return

  def execute(self, parameters, messages):

    inFeatures = parameters[0].valueAsText
    pointType = parameters[1].valueAsText

    fields = arcpy.ListFields(inFeatures)
    fieldList = []
    shpFieldName = ""

    for field in fields:
      if (field.type == "Geometry"):
        shpFieldName = field.name

      fieldList.append(field.name)
    if (not "X" in fieldList):
      arcpy.AddField_management(inFeatures, "X", "DOUBLE", 18, 11)
    if (not "Y" in fieldList):
      arcpy.AddField_management(inFeatures, "Y", "DOUBLE", 18, 11)

    calcX = "!" + shpFieldName + "!.centroid.X"
    calcY = "!" + shpFieldName + "!.centroid.Y"
    if (pointType == "TRUECENTROID"):
      calcX = "!" + shpFieldName + "!.trueCentroid.X"
      calcY = "!" + shpFieldName + "!.trueCentroid.Y"
    elif (pointType == "LABELPOINT"):
      calcX = "!" + shpFieldName + "!.labelPoint.X"
      calcY = "!" + shpFieldName + "!.labelPoint.Y"
    elif (pointType == "START"):
      calcX = "!" + shpFieldName + "!.firstPoint.X"
      calcY = "!" + shpFieldName + "!.firstPoint.Y"
    elif (pointType == "MID"):
      calcX = "!" + shpFieldName + "!.positionAlongLine(0.5,True).firstPoint.X"
      calcY = "!" + shpFieldName + "!.positionAlongLine(0.5,True).firstPoint.Y"
    elif (pointType == "END"):
      calcX = "!" + shpFieldName + "!.lastPoint.X"
      calcY = "!" + shpFieldName + "!.lastPoint.Y"

    # 2 loop... update cursor?
    arcpy.CalculateField_management(inFeatures, "X", calcX, "PYTHON_9.3")
    arcpy.CalculateField_management(inFeatures, "Y", calcY, "PYTHON_9.3")


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
    tools = AddXYField()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
