# -*- coding: utf-8 -*-
"""
按对照表设置字段别名 —— ArcGIS Pro 版

按一张「字段名-别名」对照表批量改写要素类的字段别名，用于按数据库标准批量规范字段显示名。

参数顺序（按地理处理工具原定义）：
  1. 输入表（Input Table）
  2. Output Table（Output Table）
  3. FieldInfo Table（FieldInfo Table）
  4. FieldNameField（FieldNameField）
  5. FieldAliasField（FieldAliasField）

用法：
    python run.py <Input Table> <Output Table> <FieldInfo Table> <FieldNameField> <FieldAliasField>
"""
# -*- coding: UTF-8 -*-

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


import sys
import codecs

#ツール定義

class SetFieldAliasFromTable(object):

  def __init__(self):
    self.label = "Set Field Alias from Table"
    self.description = "Set field alias from table."

    self.category = "DataManagement"
    self.canRunInBackground = False

  def getParameterInfo(self):

    param0 = arcpy.Parameter(
               displayName="Input Table",
               name="in_table",
               datatype="GPTableView",
               parameterType="Required",
               direction="Input")

    param1 = arcpy.Parameter(
        displayName="Output Table",
        name="out_table",
        datatype="GPTableView",
        parameterType="Derived",
        direction="Output")

    param1.parameterDependencies = [param0.name]
    param1.schema.clone = True

    param2 = arcpy.Parameter(
               displayName="FieldInfo Table",
               name="fieldInfoTable",
               datatype="GPTableView",
               parameterType="Required",
               direction="Input")

    param3 = arcpy.Parameter(
        displayName="FieldNameField",
        name="fieldNameField",
        datatype="Field",
        parameterType="Required",
        direction="Input")

    param3.filter.list = ['Text']
    param3.parameterDependencies = [param2.name]

    param4 = arcpy.Parameter(
        displayName="FieldAliasField",
        name="fieldAliasField",
        datatype="Field",
        parameterType="Required",
        direction="Input")

    param4.filter.list = ['Text']
    param4.parameterDependencies = [param2.name]

    params = [param0, param1, param2, param3, param4]
    return params


  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    return

  def updateMessages(self, parameters):
    return

  def execute(self, parameters, messages):
    inTable = parameters[0].valueAsText
    nameAliasTable = parameters[2].valueAsText
    nameFiled = parameters[3].valueAsText
    aliasFiled = parameters[4].valueAsText

    fields = arcpy.ListFields(inTable)

    #enc = sys.stdin.encoding
#    messages.addMessage(enc)

    fieldDict = {}

    with arcpy.da.SearchCursor(nameAliasTable, [nameFiled,aliasFiled]) as cursor:
      for row in cursor:
        fieldDict[row[0]]=row[1]

    for field in fields:
      if field.name in fieldDict:
        arcpy.AlterField_management(inTable, field.name, new_field_alias=fieldDict[field.name])


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
    tools = SetFieldAliasFromTable()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
