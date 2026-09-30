# -*- coding: utf-8 -*-
"""
添加几何哈希字段 —— ArcGIS Pro 版

为每个要素的几何计算哈希值并写入新字段，几何完全相同的要素哈希一致，用于查重、比对两版数据的图形变化。

参数顺序（按地理处理工具原定义）：
  1. Input Features（Input Features）
  2. Output Features（Output Features）

用法：
    python run.py <Input Features> <Output Features>
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
import hashlib

#ツール定義

class AddGeometryHashField(object):
  def __init__(self):
    self.label = "Add Geometry Hash Field"
    self.description = "Adds a WKB SHA256 Hash field to a feature layer."

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
        displayName="Output Features",
        name="out_features",
        datatype="GPFeatureLayer",
        parameterType="Derived",
        direction="Output")

    params = [param0, param1]
    return params

  def isLicensed(self):
    return True

  def updateParameters(self, parameters):


    return

  def updateMessages(self, parameters):
    if (parameters[0]):
      inFeatures = parameters[0].valueAsText
      if (inFeatures):
        inDesc = arcpy.Describe(inFeatures)
        if (inDesc.dataType == "FeatureLayer"):
          inDesc = inDesc.featureClass
        fields = arcpy.ListFields(inFeatures)
        for field in fields:
          if (field.name.upper() == "HASH"):
            parameters[0].setWarningMessage("The value of the [HASH] field will be overwritten.")
            break
    return

  def execute(self, parameters, messages):

    inFeatures = parameters[0].valueAsText

    fields = arcpy.ListFields(inFeatures)
    fieldList = []

    for field in fields:
      fieldList.append(field.name)

    if (not "HASH" in fieldList):
      arcpy.AddField_management(inFeatures, "HASH", "TEXT", field_length=65)

    with arcpy.da.UpdateCursor(inFeatures, ["SHAPE@WKB", "HASH"]) as cursor:
      for row in cursor:
        row[1] = hashlib.sha256(row[0]).hexdigest()
        cursor.updateRow(row)


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
    tools = AddGeometryHashField()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
