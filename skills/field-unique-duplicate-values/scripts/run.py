# -*- coding: utf-8 -*-
"""
唯一值与重复值清单 —— ArcGIS Pro 版

列出字段的全部唯一值（并可按值计数），或反向找出重复值，是代码整改与字典比对的常用手段。

参数顺序（按地理处理工具原定义）：
  1. 输入表（Input Table）
  2. 字段（可多选）（Fields）

用法：
    python run.py <Input Table> <Fields>
"""
# -*- coding: utf-8 -*-

import arcpy
import csv
import os


class UniqFieldValues(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Unique Field Values"
        self.description = "Print unique field values"
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
            multiValue=True)
        in_fields.filter.list = ['Text', 'Short', 'Long', 'Float', 'Single', 'Double']
        in_fields.parameterDependencies = [in_table.name]

        parameters = [in_table, in_fields]

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

    def constructDict(self, table, fields):
        """
        construct a dictionary with table name and field values

        Args:
            table (str): table full path.
            fields (str): field names, separated by ';'

        Returns:
            vDict (dict): a dictionary with field name key and field values
        """
        vDict = dict((fname, []) for fname in fields)
        with arcpy.da.SearchCursor(table, fields) as cursor:
            for row in cursor:
                for i in range(len(row)):
                    # can't sort None in python 3, replace None to ""
                    if row[i]:
                        vDict[fields[i]].append(row[i])
                    else:
                        vDict[fields[i]].append("")
        return vDict

    def execute(self, parameters, messages):
        """The source code of the tool."""
        fieldList = parameters[1].valueAsText.split(";")
        valueDict = self.constructDict(parameters[0].valueAsText, fieldList)
        for fname in valueDict:
            arcpy.AddMessage("\nField: {}".format(fname))
            arcpy.AddMessage("unique:")
            occurances = valueDict[fname]
            for i in sorted(set(occurances)):
                icount = occurances.count(i)
                if i is None:
                    arcpy.AddMessage("    None: 0")
                elif isinstance(i, str):
                    arcpy.AddMessage(
                        "    {}: {}".format(i.encode('utf-8').decode('utf-8', 'ignore'), icount))
                else:
                    arcpy.AddMessage("    {}: {}".format(i, icount))
        arcpy.AddMessage("    ")
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
    tools = UniqFieldValues()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
