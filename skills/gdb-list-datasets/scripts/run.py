# -*- coding: utf-8 -*-
"""
列出工作空间数据集 —— ArcGIS Pro 版

打印工作空间下所有要素类/表/要素数据集，快速了解数据结构。

参数顺序（按地理处理工具原定义）：
  1. 输入工作空间（GDB / 文件夹 / SDE）（Workspace）

用法：
    python run.py <Workspace>
"""
# -*- coding: utf-8 -*-

import arcpy
import csv
import os


class ListDatasets(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Datasets"
        self.description = "Print datasets in workspace"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_ws = arcpy.Parameter(
            displayName="Workspace",
            name="in_ws",
            datatype=["DEWorkspace","DEFeatureDataset"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        parameters = [in_ws]

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

    def codeddomainDict(self, workspace):
        """
        construct a dictionary with attribute domain code value and code desc

        Args:
            ws (str): workspace

        Returns:
            coded_dict (dict): a dictionary with code value and code desc
        """
        arcpy.env.workspace = workspace

        # dictionary - {domain name lowercase: {code value: code desc}}
        coded_dict = {}
        domains = arcpy.da.ListDomains(workspace)
        for domain in domains:
            # meta.arcpy.AddMessage('Domain name : {0}'.format(domain.name))
            if domain.domainType == 'CodedValue':
                coded_values = domain.codedValues
                temp_dict = {}
                for val, desc in coded_values.items():
                    # meta.arcpy.AddMessage('{0} : {1}'.format(val, desc))
                    temp_dict[val] = desc
                coded_dict[domain.name.lower()] = temp_dict
            elif domain.domainType == 'Range':
                temp_dict = {}
                temp_dict['min'] = domain.range[0]
                temp_dict['max'] = domain.range[1]
                coded_dict[domain.name.lower()] = temp_dict

        return coded_dict

    def execute(self, parameters, messages):
        """The source code of the tool."""
        walk = arcpy.da.Walk(parameters[0].valueAsText)
        filenamelist = []
        for dirpath, dirnames, filenames in walk:
            for filen in filenames:
                filenamelist.append(filen)

        arcpy.AddMessage("\n")
        for filename in sorted(filenamelist):
            arcpy.AddMessage("{}".format(filename))
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
    tools = ListDatasets()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
