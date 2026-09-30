# -*- coding: utf-8 -*-
"""
最小包络几何 —— ArcGIS Pro 版

为要素求最小包络几何（可选最小外接矩形/最小外接圆/包络矩形/凸包），输出面要素，用于占地范围概化、朝向分析。

参数顺序（按地理处理工具原定义）：
  1. Input Features（Input Features）
  2. Output Features（Output Features）
  3. Geometry Type（Geometry Type）

用法：
    python run.py <Input Features> <Output Features> <Geometry Type>
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

class MinimumBoundingGeometry(object):
  def __init__(self):
    self.label = "Minimum Bounding Geometry"
    self.description = "Creates a feature class containing polygons which represent a specified minimum bounding geometry enclosing each input features."

    self.category = "TransformationShapes"
    self.canRunInBackground = False

  def getParameterInfo(self):
    param0 = arcpy.Parameter(
               displayName="Input Features",
               name="in_layer",
               datatype="GPFeatureLayer",
               parameterType="Required",
               direction="Input")

    param0.filter.list = ["Multipoint","Polyline","Polygon"]

    param1 = arcpy.Parameter(
        displayName="Output Features",
        name="out_features",
        datatype="DEFeatureClass",
        parameterType="Required",
        #parameterType="Derived",
        direction="Output")

    param2 = arcpy.Parameter(
        displayName="Geometry Type",
        name="geometry_type",
        datatype="GPString",
        parameterType="Optional",
        direction="Input")

    param2.filter.type = "ValueList"
    param2.filter.list = ["RECTANGLE_BY_AREA",
                "RECTANGLE_BY_WIDTH",
                "CONVEX_HULL",
                #"CIRCLE",
                "ENVELOPE"]

    param2.value = "ENVELOPE"


    params = [param0, param1, param2]
    return params

  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    return

  def updateMessages(self, parameters):
    return

  def execute(self, parameters, messages):

    inFeatures = parameters[0].valueAsText
    outFeatures = parameters[1].valueAsText
    geometryType = parameters[2].valueAsText

    if (not geometryType):
      geometryType = "ENVELOPE"

    # arcinfo user use [MinimumBoundingGeometry_management]
    if (arcpy.ProductInfo() != "ArcInfo" or geometryType != "CONVEX_HULL"):
      arcpy.MinimumBoundingGeometry_management(inFeatures,
                                             outFeatures,
                                             geometryType)
      return

    # only CONVEX_HULL
    inDesc = arcpy.Describe(inFeatures)
    if (inDesc.dataType == "FeatureLayer"):
      inDesc = inDesc.featureClass


    dirName, fcName = os.path.split(outFeatures)

    #create output
    arcpy.CreateFeatureclass_management(dirName, fcName, "POLYGON", inFeatures, "SAME_AS_TEMPLATE", "SAME_AS_TEMPLATE", inDesc.spatialReference)

    fields = arcpy.ListFields(outFeatures)
    fieldList = []

    for field in fields:
      #messages.addMessage("{0} is a type of {1} with a length of {2}"
      #   .format(field.name, field.type, field.length))
      if (field.type != "OID" or field.type != "Geometry" ):
        fieldList.append(field.name)
    fieldList.append("SHAPE@")

    # for Progress step count
    result = arcpy.GetCount_management(inFeatures)
    count = int(result.getOutput(0))
    arcpy.SetProgressor("step", "Inserting ...", 0, count, 1)

    with arcpy.da.InsertCursor(outFeatures, fieldList) as inCursor:
      with arcpy.da.SearchCursor(inFeatures, fieldList) as cursor:
        for row in cursor:
          if (isinstance(row[-1] , arcpy.Polygon)):
            insertRow = row[:-1] + (row[-1].convexHull(),)
            inCursor.insertRow( insertRow )
          #step count
          arcpy.SetProgressorPosition()


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
    tools = MinimumBoundingGeometry()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
