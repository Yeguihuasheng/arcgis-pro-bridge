# -*- coding: utf-8 -*-
"""
检出空图层 —— ArcGIS Pro 版

扫描工作空间找出记录数为 0 的图层，交付前清垃圾用。

参数顺序（按地理处理工具原定义）：
  1. 输入工作空间（GDB / 文件夹 / SDE）（Workspace）
  2. 数据集类型（留空表示全部）（Dataset Type）

用法：
    python run.py <Workspace> <Dataset Type>
"""
# -*- coding: utf-8 -*-

import arcpy
import csv
import os


class ListEmptyDataset(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Empty Dataset"
        self.description = "Print Empty Dataset Name in Workspace (Personal Geodatabase, File Geodatabase, and SDE)"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_ws = arcpy.Parameter(
            displayName="Workspace",
            name="in_ws",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        in_datatype = arcpy.Parameter(
            displayName="Dataset Type",
            name="in_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        in_datatype.filter.list = ['FeatureClass', 'Table']

        parameters = [in_ws, in_datatype]

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

    def inventory_data(self, workspace, datatype):
        """
        Generates full path names under a catalog tree for all requested
        datatype(s).

        Parameters:
        workspace: string
            The top-level workspace that will be used.
        datatypes: string | list | tuple
            Keyword(s) representing the desired datatypes. A single
            datatype can be expressed as a string, otherwise use
            a list or tuple. See arcpy.da.Walk documentation
            for a full list.
        """
        for path, path_names, data_names in arcpy.da.Walk(workspace,
                                                          datatype = datatype):
            for data_name in data_names:
                yield os.path.join(path, data_name)

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_wspace = parameters[0].valueAsText
        in_dtype = parameters[1].valueAsText
        iList = list(self.inventory_data(in_wspace, in_dtype))
        # loop data list
        counter = 1
        for dataset in iList:
            arcpy.AddMessage("{} of {}".format(counter, len(iList)))
            result = arcpy.GetCount_management(dataset)
            if result == 0:
                arcpy.AddMessage("{}".format(dataset))
            counter += 1


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
    tools = ListEmptyDataset()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
