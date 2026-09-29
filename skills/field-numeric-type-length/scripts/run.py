# -*- coding: utf-8 -*-
"""
数值字段精度与小数位调整 —— ArcGIS Pro 版

调整数值字段的类型与长度（精度/小数位），用于面积、比例、金额等精度达标。

参数顺序（按地理处理工具原定义）：
  1. 输入表（Input Table）
  2. 字段（可多选）（Fields）
  3. 新字段类型（TEXT / LONG / DOUBLE 等）（New Field Type）
  4. 字段长度（Field Length）

用法：
    python run.py <Input Table> <Fields> <New Field Type> <Field Length>
"""
# -*- coding: utf-8 -*-

import arcpy
import csv
import os


class ChangeNumetricFieldTypAndLen(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Change Numeric Field Type and Len"
        self.description = "Change Numeric Field Type and Length. THE SCRIPT DOESN'T CHECK VALUE LENGHT."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_table = arcpy.Parameter(
            displayName="Input Table",
            name="in_table",
            datatype=["GPTableView"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        in_fields = arcpy.Parameter(
            displayName="Fields",
            name="in_fields",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        in_fields.filter.list = ['Short', 'Long', 'Float', 'Single', 'Double']
        in_fields.parameterDependencies = [in_table.name]

        in_type = arcpy.Parameter(
            displayName="New Field Type",
            name="in_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        in_type.filter.list = ['SHORT', 'LONG', 'DOUBLE', 'FLOAT']

        in_len = arcpy.Parameter(
            displayName="Field Length",
            name="in_len",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input",
            multiValue=False)

        parameters = [in_table, in_fields, in_type, in_len]

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
        # set list of OID and target field
        replace_fields = ['OID@', parameters[1].valueAsText]
        # dictionary of OID and target field value
        valueDict = {r[0]: r[1] for r in arcpy.da.SearchCursor(parameters[0].valueAsText, replace_fields)}
        # update cursor
        with arcpy.da.UpdateCursor(parameters[0].valueAsText, replace_fields) as cursor:
            arcpy.AddMessage("\n    delete {} field".format(parameters[1].valueAsText))
            arcpy.DeleteField_management(parameters[0].valueAsText, parameters[1].valueAsText)
            arcpy.AddMessage("    add {} field".format(parameters[1].valueAsText))
            if parameters[3].valueAsText:
                arcpy.AddField_management(parameters[0].valueAsText, parameters[1].valueAsText, field_type=parameters[2].valueAsText, field_length=int(parameters[3].valueAsText))
            else:
                arcpy.AddField_management(parameters[0].valueAsText, parameters[1].valueAsText,field_type=parameters[2].valueAsText)
            arcpy.AddMessage("    update field value")
            for row in cursor:
                # set value to the new field
                row[1] = valueDict[row[0]]
                cursor.updateRow(row)
        arcpy.AddMessage("\n")
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
    tools = ChangeNumetricFieldTypAndLen()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
