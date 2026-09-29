# -*- coding: utf-8 -*-
"""
修改字段类型 —— ArcGIS Pro 版

在不重建表的前提下把指定字段改写成目标类型（如文本转长整/双精度），适用于标准要求的类型整改。

参数顺序（按地理处理工具原定义）：
  1. 输入表（Input Table）
  2. 字段（可多选）（Fields）
  3. 新字段类型（TEXT / LONG / DOUBLE 等）（New Field Type）

用法：
    python run.py <Input Table> <Fields> <New Field Type>
"""
# -*- coding: utf-8 -*-

import arcpy
import csv
import os


class ChangeFieldType(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Change Field Type"
        self.description = "Change Field Type"
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
        in_fields.filter.list = ['Text', 'Short', 'Long', 'Float', 'Single', 'Double']
        in_fields.parameterDependencies = [in_table.name]

        in_type = arcpy.Parameter(
            displayName="New Field Type",
            name="in_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        paras = [in_table, in_fields, in_type]

        return paras

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, paras):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        typelist = paras[2].filter
        if paras[1].valueAsText:
            fields = [field for field in (arcpy.ListFields(paras[0].valueAsText))]
            for field in fields:
                if field.name == paras[1].valueAsText:
                    if field.type == 'String':
                        typelist.list = ['SHORT', 'LONG', 'DOUBLE', 'FLOAT']
                    else:
                        typelist.list = ['STRING']
        return

    def updateMessages(self, paras):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def is_digit(self,s):
        """
        check the list and return if all values are numeber
        https://stackoverflow.com/questions/354038/how-do-i-check-if-a-string-is-a-number-float
        :param s: list
        :return:
        """
        for textvalue in s:
            try:
                float(textvalue)
            except ValueError:
                arcpy.AddMessage("\n*******************************************")
                arcpy.AddMessage("    Text contain non-numeric value: {}".format(textvalue))
                self.getkey(textvalue)
                exit()

    def valuelen(self, fieldvalue_list):
        """
        convert numberic list to string list and return max length
        :param fieldvalue_list: list
        :return: max length
        """
        fieldvalue_list = list(map(str, fieldvalue_list))
        return len(max(fieldvalue_list, key=len))

    def getkey(self, textvalue):
        for oid, tvalue in valueDict.items():
            if tvalue == textvalue:
                arcpy.AddMessage("\n    OBJECT ID: {}    ".format(oid))

    def execute(self, paras, messages):
        """The source code of the tool."""
        tableflist = arcpy.ListFields(paras[0].valueAsText)
        for tablefield in tableflist:
            if tablefield.name == paras[1].valueAsText:
                oldftype = tablefield.type
                break

        arcpy.AddMessage("\n# {}: CONVERTING {} TO {}".format(paras[1].valueAsText, oldftype.upper(), paras[2].valueAsText))

        # set list of OID and target field
        replace_fields = ['OID@', paras[1].valueAsText]

        # dictionary of OID and target field values
        global valueDict
        valueDict= {}
        # list of OID and target field values
        fieldvaluelist = []
        with arcpy.da.SearchCursor(paras[0].valueAsText, replace_fields) as cursor:
            for row in cursor:
                valueDict[row[0]] = row[1]
                # remove Null values
                if row[1] is not None and row[1] != '':
                    fieldvaluelist.append(row[1])

        # if new field type is SHORT, LONG, DOUBLE, FLOAT
        if paras[2].valueAsText != 'STRING':
            # check input string value can be converted to int (short or long)
            if fieldvaluelist:
                self.is_digit(fieldvaluelist)
        else:
            fldlength = int(self.valuelen(fieldvaluelist)*1.3)

        with arcpy.da.UpdateCursor(paras[0].valueAsText, replace_fields) as cursor:
            arcpy.AddMessage("    - deleting field".format(paras[1].valueAsText))
            arcpy.DeleteField_management(paras[0].valueAsText, paras[1].valueAsText)
            arcpy.AddMessage("    - adding field".format(paras[1].valueAsText))
            if paras[2].valueAsText == 'STRING':
                arcpy.AddField_management(paras[0].valueAsText, paras[1].valueAsText, field_type=paras[2].valueAsText, field_length=int(fldlength))
            else:
                arcpy.AddField_management(paras[0].valueAsText, paras[1].valueAsText, field_type=paras[2].valueAsText)
            arcpy.AddMessage("    - updating field values")

            fieldtype = paras[2].value
            for row in cursor:
                # set value to the new field
                if valueDict[row[0]]:
                    # From String to Short or Long
                    if (fieldtype == 'SHORT') or (fieldtype == 'LONG'):
                        row[1] = int(valueDict[row[0]])
                    # From String to double or float
                    elif (fieldtype == 'DOUBLE') or (fieldtype == 'FLOAT'):
                        row[1] = float(valueDict[row[0]])
                    elif fieldtype == 'STRING':
                        row[1] = str(valueDict[row[0]]).split(".")[0]
                else:
                    row[1] = None

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
    tools = ChangeFieldType()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
