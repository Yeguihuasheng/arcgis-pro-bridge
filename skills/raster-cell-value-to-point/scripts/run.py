# -*- coding: utf-8 -*-
"""
栅格像元转点 —— ArcGIS Pro 版

把栅格的每个有效像元转成点并把像元值写入属性，用于栅格取样、把连续表面离散成观测点。

参数顺序（按地理处理工具原定义）：
  1. Input Raster（Input Raster）
  2. Input Features（Input Features）
  3. Output Features（Output Features）

用法：
    python run.py <Input Raster> <Input Features> <Output Features>
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


#ツール定義

class RasterCellValueToPoint(object):
  def __init__(self):
    self.label = "Raster Cell Value to Point Attribute"
    self.description = "Set Point Attributes from Raster Pixcel value."

    self.category = "Fields"
    self.canRunInBackground = False

  def getParameterInfo(self):
    param0 = arcpy.Parameter(
    displayName="Input Raster",
    name="in_raster",
    datatype="GPRasterLayer",
    parameterType="Required",
    direction="Input")

    param1 = arcpy.Parameter(
      displayName="Input Features",
      name="in_features",
      datatype="GPFeatureLayer",
      parameterType="Required",
      direction="Input")

    param2 = arcpy.Parameter(
      displayName="Output Features",
      name="out_features",
      datatype="GPFeatureLayer",
      parameterType="Derived",
      direction="Output")

    param2.parameterDependencies = [param1.name]
    param2.schema.clone = True

    return [param0, param1, param2]

  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    return

  def updateMessages(self, parameters):
    raster = parameters[0].valueAsText
    feature = parameters[1].valueAsText

    if (feature and raster):
      inDesc = arcpy.Describe(feature)
      if (inDesc.dataType == "FeatureLayer"):
        inDesc = inDesc.featureClass

      parameters[0].clearMessage()

      desc = arcpy.Describe(raster)
      for bandIndex in range(desc.bandCount):
        fname = 'BAND' + str(bandIndex)

        fields = arcpy.ListFields(feature)
        for field in fields:
          if (field.name.upper() == fname):
            parameters[1].setWarningMessage("The value of the [band n] field will be overwritten.")
            break

    return

  def execute(self, parameters, messages):
    raster = parameters[0].valueAsText
    feature = parameters[1].valueAsText

    fields = arcpy.ListFields(feature)
    fieldList = [field.name for field in fields]

    addFields = []
    desc = arcpy.Describe(raster)
    for bandIndex in range(desc.bandCount):
      fname = 'BAND' + str(bandIndex)
      addFields.append(fname)
      if (not fname in fieldList):
        arcpy.AddField_management(feature, fname, "DOUBLE", 18, 11)

      addFields.append('SHAPE@XY')
      bandIndex=';'.join( str(x) for x in range(1,desc.bandCount + 1))

    with arcpy.da.UpdateCursor(feature, addFields) as cursor:
      for row in cursor:

        fname = 'BAND' + str(bandIndex)
        result = arcpy.GetCellValue_management(raster, str((row[-1])[0]) + " " + str((row[-1])[1]), bandIndex)

        res = result.getOutput(0).split('\\n')

        for inx in range(len(res)):
          cellValue = float(res[inx])
          row[inx] = cellValue
        #Update the FC row
        cursor.updateRow(row)
    return


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
    tools = RasterCellValueToPoint()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
