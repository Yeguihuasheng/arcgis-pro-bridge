# -*- coding: utf-8 -*-
"""
两个数据集模式一致性检查 —— ArcGIS Pro 版

逐字段比对两个数据集的字段名、类型、别名，输出不一致项，用于入库前后、或不同批次成果之间的结构校验。

参数顺序（按地理处理工具原定义）：
  1. 输入表（可多个）（Input Tables）
  2. 对照用的目标表（可多个）（Target Tables）

用法：
    python run.py <Input Tables> <Target Tables>
"""
# -*- coding: utf-8 -*-

import arcpy
import csv
import os


class SchemaCheck(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Check Schema"
        self.description = "Check schema between two datasets"
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
            multiValue=False)

        target_tables = arcpy.Parameter(
            displayName="Target Tables",
            name="target_tables",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        parameters = [in_tables, target_tables]

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

    def compareIntersect(self, x, y):
        return frozenset(x).intersection(y)

    def compareDifference(self, x, y):
        return frozenset(x).difference(y)

    def makeFieldDict(self, input_layer):
        lFields = arcpy.ListFields(input_layer)

        fieldDict = dict()
        for lf in lFields:
            # change filenames to lower case
            fieldDict[lf.name.lower()] = [lf.type, lf.length]
        return fieldDict

    def baseName(self, input_layer, target_layer):
        """
        return input and target data basename.
        Parameters:
        input_layer: string
            input data full path. ex) C:\\Works\\GEODB\Data.gdb\\PublicPt
        target_layer: string
            target data full path. ex) Database Connections\\Connection to
            SDE.sde\\SDE.PublicPt
        """
        if ".sde" in input_layer:
            # remove schema from name
            in_name = arcpy.Describe(input_layer).baseName.split(".")[1]
        else:
            in_name = arcpy.Describe(input_layer).baseName
        if ".sde" in target_layer:
            tar_name = arcpy.Describe(target_layer).baseName.split(".")[1]
        else:
            tar_name = arcpy.Describe(target_layer).baseName
        return in_name, tar_name

    def checkSchema(self, input_layer, target_layer):
        """
        check schema of input and target dataset
        """
        skipfieldname = ['shape_length', 'shape_area', 'shape.len',
                         'shape.area', 'shape']
        arcpy.AddMessage("****** Checking Schema ******")
        input_dict = self.makeFieldDict(input_layer)
        target_dict = self.makeFieldDict(target_layer)

        tnames = self.baseName(input_layer, target_layer)

        # fields in both dataset
        combinedfield_list = (
            self.compareIntersect(input_dict.keys(), target_dict.keys()))
        arcpy.AddMessage("\n** Checking Fields List")
        # fields not in input
        missingfieldInputlist = sorted([x for x in (
            self.compareDifference(target_dict.keys(), input_dict.keys()))])
        # fields not in target
        missingfieldTargetlist = sorted([x for x in (
            self.compareDifference(input_dict.keys(), target_dict.keys()))])

        if (len(missingfieldTargetlist) + len(missingfieldInputlist)) == 0:
            arcpy.AddMessage("  - All fields are presented in input and "
                             "target")
        else:
            arcpy.AddMessage("  - Field not in input ({}):".format(tnames[0]))
            fname_list = []
            for i in missingfieldInputlist:
                if i.lower() not in skipfieldname:
                    arcpy.AddMessage("    {}".format(i.upper()))
                    fname_list.append(str(i).upper())
            arcpy.AddMessage(fname_list)
            arcpy.AddMessage(" ")

            arcpy.AddMessage("  - Field not in target ({}):".format(tnames[1]))
            fname_list = []
            for i in missingfieldTargetlist:
                if i.lower() not in skipfieldname:
                    arcpy.AddMessage("    {}".format(i.upper()))
                    fname_list.append(str(i).upper())
            arcpy.AddMessage(fname_list)
        arcpy.AddMessage("\n")

        # check field type
        arcpy.AddMessage("\n** Checking Field Type")
        fieldtypeList = [i for i in combinedfield_list if
                         input_dict[i][0] != target_dict[i][0]]
        if fieldtypeList:
            arcpy.AddMessage("  - Found type mismatch in common fields")
            for i in fieldtypeList:
                arcpy.AddMessage("    Field:{}".format(i))
                arcpy.AddMessage(
                    "    Input:{} - Len:{}, Target:{} - Len:{}".format(
                        input_dict[i][0], input_dict[i][1], target_dict[i][0],
                        target_dict[i][1]))
            arcpy.AddMessage("    Total {} field(s) type mismatch found".format(
                len(fieldtypeList)))
        else:
            arcpy.AddMessage("  - No field type mismatch in common fields")
        arcpy.AddMessage("\n")

        # check field length
        arcpy.AddMessage("\n** Checking Field Lenght")
        fieldlenList = [i for i in combinedfield_list if
                        input_dict[i][1] != target_dict[i][1]]
        if fieldlenList:
            arcpy.AddMessage("  - Found length mismatch in common fields")
            for i in fieldlenList:
                arcpy.AddMessage("    Field:{}".format(i))
                arcpy.AddMessage(
                    "    Input:{}, Target:{}".format(input_dict[i][1],
                                                   target_dict[i][1]))
            arcpy.AddMessage("    Total {} field(s) lenght mismatch "
                             "found".format(
                len(fieldlenList)))
        else:
            arcpy.AddMessage("  - No field lenght mismatch in common fields")
        arcpy.AddMessage("\n")

        # check record count
        arcpy.AddMessage("\n** Checking Record Count")
        input_row_count = int(
            arcpy.GetCount_management(input_layer).getOutput(0))
        target_row_count = int(
            arcpy.GetCount_management(target_layer).getOutput(0))
        arcpy.AddMessage('  - Total input number of records: {}'.format(
            '{0:,}'.format(input_row_count)))
        arcpy.AddMessage('  - Total target number of records: {}'.format(
            '{0:,}'.format(target_row_count)))
        arcpy.AddMessage("\n\n")

    def execute(self, parameters, messages):
        """The source code of the tool."""

        in_tables = parameters[0].valueAsText
        target_tables = parameters[1].valueAsText

        names = self.baseName(in_tables, target_tables)
        arcpy.AddMessage("****** Checking Data Name ******")
        if names[0] == names[1]:
            arcpy.AddMessage("Input and Target have same name\n\n")
        else:
            arcpy.AddMessage("Input and Target have different Name")
            arcpy.AddMessage("{} : {}\n\n".format(names[0], names[1]))

        self.checkSchema(in_tables, target_tables)

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
    tools = SchemaCheck()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
