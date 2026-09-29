# -*- coding: utf-8 -*-
"""
列出 MXD 数据源清单 —— ArcGIS Pro 版

逐个图层列出地图文档的数据源路径（可整文件夹扫描），用于交付前的断链检查与数据源台账。

参数顺序（按地理处理工具原定义）：
  1. 输入 MXD 地图文档（可多个）（Input MXDs）
  2. 输出 CSV 文件路径（Output CSV File）

用法：
    python run.py <Input MXDs> <Output CSV File>
"""
# -*- coding: utf-8 -*-

import arcpy
import csv
import os


class ListDataSourcesMXDs(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Data Sources MXDs"
        self.description = "List layer's data source from MXDs"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_mxds = arcpy.Parameter(
            displayName="Input MXDs",
            name="in_mxds",
            datatype="DEFile",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        in_mxds.filter.list = ['mxd']

        out_csv = arcpy.Parameter(
            displayName="Output CSV File",
            name="out_csv",
            datatype="DEFile",
            parameterType="Required",
            direction="Output",
            multiValue=False)
        out_csv.filter.list = ['csv']
        parameters = [in_mxds, out_csv]

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

    def crawlmxds(self, in_mxds):
        for counter, in_mxd in enumerate(in_mxds, start=1):
            # when mxd file name has a space, arcgis input add "'" and need to remove it
            in_mxd = in_mxd.strip("'")
            arcpy.AddMessage("\n#{} of {}: {}".format(counter, len(in_mxds), in_mxd))
            mxd = arcpy.mapping.MapDocument(in_mxd)
            dataframes = arcpy.mapping.ListDataFrames(mxd)
            for df in dataframes:
                dfDesc = df.description if df.description != "" else "None"
                layers = arcpy.mapping.ListLayers(mxd, "", df)
                for lyr in layers:
                    lyrName = lyr.name
                    lyrDatasource = lyr.dataSource if lyr.supports(
                        "dataSource") else "N/A"
                    seq = (in_mxd, df.name, dfDesc, lyrName, lyrDatasource);
                    yield seq
            del mxd

    def execute(self, parameters, messages):
        """The source code of the tool."""
        inMXDs = parameters[0].valueAsText.split(";")
        outCSV = parameters[1].valueAsText
        with open(outCSV, "wb") as f:
            w = csv.writer(f)
            header = ("MXD Path", "DataFrame Name", "DataFrame Description",
                      "Layer name", "Layer Datasource")
            w.writerow(header)
            rows = self.crawlmxds(inMXDs)
            w.writerows(rows)
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
    tools = ListDataSourcesMXDs()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
