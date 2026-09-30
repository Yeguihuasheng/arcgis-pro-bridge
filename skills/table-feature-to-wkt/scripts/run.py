# -*- coding: utf-8 -*-
"""
要素转 WKT 文本表 —— ArcGIS Pro 版

把要素类的几何转成 WKT 文本并连同属性导出为 CSV，用于与非 GIS 系统交换图形、文本方式备份几何。

参数顺序（按地理处理工具原定义）：
  1. Input Features（Input Features）
  2. Output CSV（Output CSV）

用法：
    python run.py <Input Features> <Output CSV>
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


import re
import os
import codecs

#ツール定義

class FeatureToWKTCSV(object):

  def __init__(self):
    self.label = "Feature To UTF-8 WKT CSV"
    self.description = "Creates a UTF-8 WKT CSV from specified features."

    self.category = "DataManagement"
    self.canRunInBackground = False

  def getParameterInfo(self):

    param0 = arcpy.Parameter(
               displayName="Input Features",
               name="in_layer",
               datatype="GPFeatureLayer",
               parameterType="Required",
               direction="Input")

    param0.filter.list = ["Point", "Multipoint", "Polyline", "Polygon"]

    param1 = arcpy.Parameter(
        displayName="Output CSV",
        name="out_csv",
        datatype="DEFile",
        parameterType="Required",
        #parameterType="Derived",
        direction="Output")
    param1.filter.list = ['csv', 'txt']

    params = [param0, param1]
    return params


  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    return

  def updateMessages(self, parameters):
    return

  def execute(self, parameters, messages):
    inFeatures = parameters[0].valueAsText
    outCsv = parameters[1].valueAsText

    inDesc = arcpy.Describe(inFeatures)
    if (inDesc.dataType == "FeatureLayer"):
      inDesc = inDesc.featureClass

    fields = arcpy.ListFields(inFeatures)
    shpField = ""
    fieldList = []
    typeList = []

    for field in fields:
      if (field.type == "Geometry"):
        shpField = field.name
      else:
        fieldList.append(field.name)
        typeList.append(field.type)

    fieldList.append("SHAPE@WKT")

    with arcpy.da.SearchCursor(inFeatures, fieldList) as cursor:
      with codecs.open(outCsv, 'w', 'utf-8') as csvFile:
        #header
        for field in fieldList:
          if field != "SHAPE@WKT":
            csvFile.write( field )
            csvFile.write( "," )
          else:
            csvFile.write( "WKT" )
        csvFile.write( '\r\n' )

        isFirstTime = True
        for row in cursor:
          if (isFirstTime):
            isFirstTime = False
          else:
            csvFile.write( '\r\n' )

          index = 0
          for ftype in typeList:
            val = row[index]
            if ftype != 'SmallInteger' \
               and ftype != 'Integer' \
               and ftype != 'Single' \
               and ftype != 'Double' \
               and ftype != 'OID':
              csvFile.write( '"' )
              if val in '"':
                val = val.replace('"', '""')
              csvFile.write( val )
              csvFile.write( '"' )
            else:
              csvFile.write( str(val) )

            csvFile.write( ',' )

            index=index+1
            #end loop field
          if row[-1]:
            csvFile.write( '"' )
            csvFile.write( re.sub( '\r\n|\n|\r', '', row[-1] ) )
            csvFile.write( '"' )
          else:
            messages.addWarningMessage( str(row[0]) + " None Geometry")


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
    tools = FeatureToWKTCSV()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
