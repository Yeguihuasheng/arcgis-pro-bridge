# -*- coding: utf-8 -*-
"""
生成随机采样点 —— ArcGIS Pro 版

在指定范围（面要素或图层范围）内生成给定数量的随机点，输出点要素类，用于抽样调查、精度验证布点。

参数顺序（按地理处理工具原定义）：
  1. Input Features（Input Features）
  2. Point Count Field（Point Count Field）
  3. Point Count [If not field]（Point Count [If not field]）
  4. Output Features（Output Features）

用法：
    python run.py <Input Features> <Point Count Field> <Point Count [If not field]> <Output Features>
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

import numpy as np

#ツール定義

class RandomPoints(object):

  def __init__(self):
    self.label = "Random Points"
    self.description = "Creates a specified number of random point features. Random points can be generated in a inside polygon features."

    self.category = "TransformationShapes"
    self.canRunInBackground = False

  def getParameterInfo(self):

    param0 = arcpy.Parameter(
        displayName="Input Features",
        name="in_layer",
        datatype="GPFeatureLayer",
        parameterType="Required",
        direction="Input")
    param0.filter.list = ["Polygon"]

    param1 = arcpy.Parameter(
        displayName="Point Count Field",
        name="in_rndPointNumCol",
        datatype="Field",
        parameterType="Optional",
        direction="Input")

    param1.filter.list = ['Short', 'Long']
    param1.parameterDependencies = [param0.name]


    param2 = arcpy.Parameter(
        displayName="Point Count [If not field]",
        name="in_rndPointNum",
        datatype="GPLong",
        parameterType="Required",
        direction="Input")
    param2.value = 100

    param3 = arcpy.Parameter(
        displayName="Output Features",
        name="out_features",
        datatype="DEFeatureClass",
        parameterType="Required",
        direction="Output")

    return [param0, param1, param2, param3]

  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    return

  def updateMessages(self, parameters):
    return

  def execute(self, parameters, messages):
    try:
      layer = parameters[0].value
      cntCol = parameters[1].valueAsText
      pntNum = parameters[2].value
      outFullName = parameters[3].valueAsText

      #messages.addMessage(layer.name)
      #if not (cntCol is None):
      #  messages.addMessage(cntCol)
      #messages.addMessage(outFullName)

      geomType = "POINT"
      template = None
      outWs = os.path.dirname(outFullName)
      outFc = os.path.basename(outFullName)

      # messages.addMessage("WS:{0} / Name:{1}".format(outWs,outFc))
      has_m = "DISABLED"
      has_z = "DISABLED"
      spRef = None

      dataset = layer.dataSource
      spRef = arcpy.Describe(dataset).spatialReference

      arcpy.CreateFeatureclass_management(outWs, outFc, geomType, template, has_m, has_z, spRef)
      arcpy.AddField_management(outFullName, "orgOid", "LONG", 10, "", "", "OriginalOID", "NON_NULLABLE")

      oidCol = arcpy.Describe(layer).OIDFieldName
      outcols = [oidCol,"SHAPE@"]
      if not (cntCol is None):
        outcols.append(cntCol)

      # for Progress step count
      result = arcpy.GetCount_management(layer)
      count = int(result.getOutput(0))
      arcpy.SetProgressor("step", "Inserting ...", 0, count, 1)

      with arcpy.da.SearchCursor(layer, outcols) as cursor, arcpy.da.InsertCursor(outFullName, ["orgOid","SHAPE@"]) as ins:
        for row in cursor:
          x = 0
          loopCnt = pntNum
          if not (cntCol is None) and not (row[2] is None):
            loopCnt = row[2]

          while x < loopCnt:
            px = row[1].extent.XMin + row[1].extent.width * np.random.random()
            py = row[1].extent.YMin + row[1].extent.height * np.random.random()
            pt = arcpy.Point(px,py)

            #caution: loop end is contains == true
            if row[1].contains(pt):
              x += 1
              ins.insertRow([ row[0], pt ])
          # step count
          arcpy.SetProgressorPosition()

    except Exception as e:
      messages.AddErrorMessage(e.message)


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
    tools = RandomPoints()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
