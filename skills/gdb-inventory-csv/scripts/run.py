# -*- coding: utf-8 -*-
"""
工作空间数据清单导出 CSV —— ArcGIS Pro 版

把文件地理数据库/个人库/SDE 工作空间内的全部要素类与表清点成 CSV 清单（路径、要素数据集、名称、几何类型），用于交付前盘库与成果核对。

参数顺序（按地理处理工具原定义）：
  1. 输入工作空间（GDB / 文件夹 / SDE）（Workspace）
  2. 输出 CSV 文件路径（Output CSV File）

用法：
    python run.py <Workspace> <Output CSV File>
"""
# -*- coding: utf-8 -*-

import arcpy
import csv
import os


class WSInventory(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Workspace Data Inventory to CSV"
        self.description = "Create CSV file with inventory (full path, feature dataset name, dataset name, shape type) of Workspace (Personal Geodatabase, File Geodatabase, and SDE)"
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

        out_csv = arcpy.Parameter(
            displayName="Output CSV File",
            name="out_csv",
            datatype="DEFile",
            parameterType="Required",
            direction="Output",
            multiValue=False)
        out_csv.filter.list = ['csv']
        parameters = [in_ws, out_csv]

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

    def inventory_data(self, workspace, datatypes):
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
        for path, path_names, data_names in arcpy.da.Walk(workspace, datatype=datatypes):
            for data_name in data_names:
                yield os.path.join(path, data_name)

    def crawldb(self, input_workspace):
        """
        Generates iterator of full path, feature dataset name, dataset name, shape type for every dataset in workspace.

        Parameters:
        workspace: string
            The top-level workspace that will be used.
        """
        # loop data list
        for dataset in self.inventory_data(input_workspace, "Any"):
            # check if data is accessable/readable
            if arcpy.Exists(dataset):
                # Create a Describe object
                desc = arcpy.Describe(dataset)
                # dataset name
                dataset_basename = desc.baseName
                # dataset type
                dataset_type = desc.dataType
                # if dataset is feature class
                if dataset_type == "FeatureClass":
                    # fc path
                    fcHome = os.path.dirname(dataset)
                    # if feature class is inside feature dataset
                    if arcpy.Describe(fcHome).dataType == "FeatureDataset":
                        # return feature dataset name
                        dataset_featuredataset = os.path.basename(fcHome)
                    else:
                        dataset_featuredataset = ""
                    # dataset shape type
                    dataset_shape = desc.shapeType
                else:
                    dataset_shape = ""
                    dataset_featuredataset = ""
                # create tuple
                seq = (dataset, dataset_featuredataset, dataset_basename, dataset_type, dataset_shape)
                yield seq

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_wspace = parameters[0].valueAsText
        arcpy.AddMessage("{}".format(in_wspace))
        out_csv = parameters[1].valueAsText
        with open(out_csv, 'wb') as f:
            # set csv writer object
            w = csv.writer(f)
            # set csv header
            header = ("Source", "FeatureDataset", "TableName", "DatasetType", "ShapeType")

            w.writerow(header)
            rows = self.crawldb(in_wspace)
            for i in rows:
                w.writerow(i)

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
    tools = WSInventory()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
