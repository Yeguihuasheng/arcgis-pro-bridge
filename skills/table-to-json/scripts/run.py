# -*- coding: utf-8 -*-
"""
表/图层导出 JSON —— ArcGIS Pro 版

把表或要素图层的记录导出为 JSON 文件，用于前后端数据交换、接口联调取数。

参数顺序（按地理处理工具原定义）：
  1. In Records（In Records）
  2. Output JSON（Output JSON）

用法：
    python run.py <In Records> <Output JSON>
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

class TableLayerToJSON(object):

  def __init__(self):
    self.label = "Table/Layer to JSON"
    self.description = "Creates a esri JSON."

    self.category = "DataManagement"
    self.canRunInBackground = False

  def getParameterInfo(self):

    param0 = arcpy.Parameter(
               displayName="In Records",
               name="in_layer",
               datatype=["GPFeatureLayer" , "GPTableView"],
               parameterType="Required",
               direction="Input")

    param1 = arcpy.Parameter(
        displayName="Output JSON",
        name="out_JSON",
        datatype="DEFile",
        parameterType="Required",
        #parameterType="Derived",
        direction="Output")
    param1.filter.list = ['json', 'txt']

    params = [param0, param1]
    return params


  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    return

  def updateMessages(self, parameters):
    return

  def execute(self, parameters, messages):

    records = parameters[0].valueAsText
    outJSON = parameters[1].valueAsText

    inDesc = arcpy.Describe(records)
    if (inDesc.dataType == "FeatureLayer"):
      arcpy.FeaturesToJSON_conversion(records, outJSON)
      return

    fieldTypeDict = { "SmallInteger":"esriFieldTypeSmallInteger",
  "Integer":"esriFieldTypeInteger",
  "Single:":"esriFieldTypeSingle",
  "Double":"esriFieldTypeDouble",
  "String":"esriFieldTypeString",
  "Date":"esriFieldTypeDate",
  "OID":"esriFieldTypeOID",
  "Geometry":"esriFieldTypeGeometry",
  "Blob":"esriFieldTypeBlob",
  "Raster":"esriFieldTypeRaster",
  "Guid:":"esriFieldTypeGUID",
  "GlobalID":"esriFieldTypeGlobalID" }

    fields = arcpy.ListFields(records)
    fieldList = [field.name for field in fields]

    with arcpy.da.SearchCursor(records, fieldList) as cursor:
      with codecs.open(outJSON, 'w', 'utf-8') as jsonFile:

        jsonFile.write('{ "displayFieldName": "", ')
        jsonFile.write('"fieldAliases": {')
        lstString = []
        for field in fields:
          lstString.append( '"{}":"{}"'.format(field.name, field.aliasName) )
        jsonFile.write( ','.join(lstString) )

        jsonFile.write('},') # end fieldAliases

        jsonFile.write('"fields": [')
        for index in range(len(fields)):
          field = fields[index]

          jsonFile.write("{")
          jsonFile.write('"name":"{}",'.format(field.name) )
          jsonFile.write('"type":"{}",'.format(fieldTypeDict[field.type]) )
          jsonFile.write('"alias":"{}",'.format(field.aliasName) )
          jsonFile.write('"length":"{}"'.format(field.length) )
          jsonFile.write("}")
          if (index != len(fields)-1):
            jsonFile.write(",")

        jsonFile.write('],') # end field

        jsonFile.write('"features": [')

        isFirstTime = True
        for row in cursor:
          if (isFirstTime):
            isFirstTime = False
          else:
            jsonFile.write( ',' )

          jsonFile.write('{ "attributes": {')
          #lstRow = []
          for index in range(len(row)):
            #lstRow.append(str(record))

            jsonFile.write( '"' )
            jsonFile.write( fields[index].name )
            jsonFile.write( '":' )
            if (fields[index].type == "String"):
              #messages.addMessage(row[index])
              jsonFile.write( '"' )
              jsonFile.write( row[index] )
              jsonFile.write( '"' )
              #lstRow.append( '"{}"'.format(row[index].encode('utf-8')))
            elif (fields[index].type == "Date"):
              EPOCH = datetime.datetime(1970, 1, 1, tzinfo = None) #tzinfo=pytz.timezone('utc'))
              epochMsec = int((row[index] - EPOCH).total_seconds() / 1000)
              jsonFile.write( str(epochMsec) )
            else:
              #lstRow.append( '{}'.format(row[index]))
              jsonFile.write( '{}'.format(row[index]) )
            if (index != len(row)-1):
              jsonFile.write( ',' )

          #jsonFile.write( ','.join(lstRow) )

          jsonFile.write('} }')
        jsonFile.write('] }') #end features


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
    tools = TableLayerToJSON()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
