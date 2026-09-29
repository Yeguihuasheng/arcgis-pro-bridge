# -*- coding: utf-8 -*-
"""
字段名转大写 —— ArcGIS Pro 版

把要素类/表的所有字段名统一改为大写，满足部分地方入库标准的命名要求。

参数顺序（按地理处理工具原定义）：
  1. 输入表（Input Table）
  2. 输出位置（工作空间或文件夹）（Output Location）
  3. 输出表名（Output Table Name）

用法：
    python run.py <Input Table> <Output Location> <Output Table Name>
"""
# -*- coding: utf-8 -*-

import arcpy
import csv
import os


class UpperCase(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Field Name To Upper Case"
        self.description = "Change field name to all upper case"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_table = arcpy.Parameter(
            displayName="Input Table",
            name="in_table",
            datatype=["GPFeatureLayer", "DETable"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        out_ws = arcpy.Parameter(
            displayName="Output Location",
            name="out_ws",
            datatype=["DEWorkspace", "DEFeatureDataset"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        out_table = arcpy.Parameter(
            displayName="Output Table Name",
            name="out_table",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        parameters = [in_table, out_ws, out_table]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        listFields = arcpy.ListFields(parameters[0].valueAsText)

        fms = arcpy.FieldMappings()
        for i in listFields:
            if i.type not in ["OID", "Geometry", "GlobalID", "Guid"]:
                fm = arcpy.FieldMap()
                fm.addInputField(parameters[0].valueAsText, i.name)
                newField = fm.outputField
                newField.name = i.name.upper()
                fm.outputField = newField
                fms.addFieldMap(fm)

        desc = arcpy.Describe(parameters[0].valueAsText)
        if desc.dataType == "FeatureClass":
            arcpy.FeatureClassToFeatureClass_conversion(parameters[0].valueAsText, parameters[1].valueAsText, parameters[2].valueAsText, field_mapping=fms)
        elif desc.dataType == "Table":
            arcpy.TableToTable_conversion(parameters[0].valueAsText, parameters[
                1].valueAsText, parameters[2].valueAsText, field_mapping=fms)
        arcpy.AddMessage("  ")
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
    tools = UpperCase()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
