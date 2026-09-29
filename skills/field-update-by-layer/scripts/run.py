# -*- coding: utf-8 -*-
"""
按另一图层更新字段 —— ArcGIS Pro 版

用另一图层的同名字段回写当前图层（等价于「挂接+字段计算」但不落地中间结果），适合属性批量赋值。

参数顺序（按地理处理工具原定义）：
  1. 输入数据集（要素类或 shapefile）（Input Dataset (feature class or shapefile)）
  2. 输入图层的连接字段（Input Join Field）
  3. 需要被更新的字段（Input Update Field）
  4. 连接表（Join Table）
  5. 连接表的字段（Join Table Field）
  6. 连接表的参考字段（Join Reference Field）

用法：
    python run.py <Input Dataset (feature class or shapefile)> <Input Join Field> <Input Update Field> <Join Table> <Join Table Field> <Join Reference Field>
"""
# -*- coding: utf-8 -*-

import arcpy
import csv
import os


class UpdateField(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Update Field based on another layer"
        self.description = "Update field based on the field from another " \
                           "layer (alternative to join and field " \
                           "calculate)"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_table = arcpy.Parameter(
            displayName="Input Dataset (feature class or shapefile)",
            name="in_table",
            datatype=['DEFeatureClass', 'DEShapefile'],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        input_join_field = arcpy.Parameter(
            displayName="Input Join Field",
            name="input_join_field",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        input_join_field.filter.list = ['Text', 'Short', 'Long', 'Float', 'Single', 'Double']
        input_join_field.parameterDependencies = [in_table.name]

        input_update_field = arcpy.Parameter(
            displayName="Input Update Field",
            name="input_update_field",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        input_update_field.filter.list = ['Text', 'Short', 'Long', 'Float', 'Single', 'Double']
        input_update_field.parameterDependencies = [in_table.name]

        join_table = arcpy.Parameter(
            displayName="Join Table",
            name="join_table",
            datatype=["GPTableView"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        join_table_field = arcpy.Parameter(
            displayName="Join Table Field",
            name="join_table_field",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        join_table_field.filter.list = ['Text', 'Short', 'Long', 'Float', 'Single', 'Double']
        join_table_field.parameterDependencies = [join_table.name]

        join_ref_field = arcpy.Parameter(
            displayName="Join Reference Field",
            name="join_ref_field",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        join_ref_field.filter.list = ['Text', 'Short', 'Long', 'Float', 'Single', 'Double']
        join_ref_field.parameterDependencies = [join_table.name]

        parameters = [in_table, input_join_field, input_update_field,
                      join_table, join_table_field, join_ref_field]

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

    def createDict(self, fc, fields):
        """
        construct a dictionary with unique id and target field values
        Args:
            table (str): table full path.
            fields (str): list with field names
        Returns:
            vDict (dict): a dictionary with unique id key and field values
        """
        attr_dict = {}
        # loop source feature class
        with arcpy.da.SearchCursor(fc, fields) as cursor:
            for row in cursor:
                attr_dict[row[0]] = row[1]
        return attr_dict


    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.AddMessage("- create data dictionary")
        valueDict = self.createDict(parameters[3].valueAsText, [parameters[4].valueAsText,
                                                                parameters[5].valueAsText])
        # set workspace
        arcpy.AddMessage("- set workspace")
        desc = arcpy.Describe(parameters[0])
        ws = desc.path
        desc1 = arcpy.Describe(ws)
        if hasattr(desc1, "datasetType") and desc1.datasetType=='FeatureDataset':
            ws = desc1.path

        count = len(list(i for i in
                         arcpy.da.SearchCursor(desc.catalogPath, ["OBJECTID"])))

        arcpy.AddMessage("- check if the input dataset is versioned")
        if desc.isVersioned:
            # Start an edit session. Must provide the workspace.
            arcpy.AddMessage("- start an edit session")
            edit = arcpy.da.Editor(ws)

            # Edit session is started without an undo/redo stack for
            # versioned data
            #  (for second argument, use False for unversioned data)
            edit.startEditing(False, True)

            # Start an edit operation
            edit.startOperation()

            # Update a row into the table.
            arcpy.AddMessage("- update the table")
            with arcpy.da.UpdateCursor(desc.catalogPath,
                                       [parameters[1].valueAsText, parameters[2].valueAsText]) as \
                    cursor:
                ten_list = [x for x in range(10, 100, 10)]
                for counter, row in enumerate(cursor, start = 1):
                    percent = int(counter * 100 / count)
                    if percent in ten_list:
                        ten_list.remove(percent)
                        arcpy.AddMessage('{} percent complete'.format(percent))
                    if row[0] in valueDict.keys():
                        row[1] = valueDict[row[0]]
                        cursor.updateRow(row)
                del row, cursor

            # Stop the edit operation.
            edit.stopOperation()

            # Stop the edit session and save the changes
            arcpy.AddMessage("- stop the edit session and save the changes")
            edit.stopEditing(True)

        else:
            # Update a row into the table.
            arcpy.AddMessage("- update the table")
            with arcpy.da.UpdateCursor(desc.catalogPath,
                                       [parameters[1].valueAsText, parameters[2].valueAsText]) as \
                    cursor:
                ten_list = [x for x in range(10, 100, 10)]
                for counter, row in enumerate(cursor, start = 1):
                    percent = int(counter * 100 / count)
                    if percent in ten_list:
                        ten_list.remove(percent)
                        arcpy.AddMessage('{} percent complete'.format(percent))
                    if row[0] in valueDict.keys():
                        row[1] = valueDict[row[0]]
                        cursor.updateRow(row)
                del row, cursor


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
    tools = UpdateField()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
