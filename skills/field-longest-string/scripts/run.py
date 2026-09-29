# -*- coding: utf-8 -*-
"""
查找最长字符串值 —— ArcGIS Pro 版

扫描文本字段求出最长串及其长度，为设置字段长度提供依据。

参数顺序（按地理处理工具原定义）：
  1. 输入表（可多个）（Input Tables）

用法：
    python run.py <Input Tables>
"""
# -*- coding: utf-8 -*-

import arcpy
import csv
import os


class LongestString(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Longest String"
        self.description = "List the longest string in Tables and Feature Classes"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_tables = arcpy.Parameter(
            displayName="Input Tables",
            name="in_tables",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        parameters = [in_tables]

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
        in_tables = parameters[0].valueAsText.split(";")
        for counter, intable in enumerate(in_tables, start=1):
            intable = intable.replace("'", "")
            arcpy.AddMessage('\n# {} of {}: {}'.format(
                counter, len(in_tables), intable))
            fieldnames = [field.baseName for field in
                          arcpy.ListFields(intable, field_type='String')]
            for counter, fieldname in enumerate(fieldnames):
                arcpy.AddMessage(
                    "{} of {}: {}".format(counter + 1, len(fieldnames),
                                          fieldname))
                with arcpy.da.SearchCursor(intable, fieldname) as cursor:
                    fieldvalue_list = [row[0] for row in cursor if
                                       row[0] is not None]
                if fieldvalue_list:
                    arcpy.AddMessage("    longest string: {}".format(
                        len(max(fieldvalue_list, key=len))))
                    arcpy.AddMessage("    {}".format(
                        max(fieldvalue_list, key=len).encode(
                            'utf-8').decode('utf-8', 'ignore')))  # add encode to fix unicode error
                else:
                    arcpy.AddMessage("    EMPTY FIELD")
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
    tools = LongestString()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
