# -*- coding: utf-8 -*-
"""
列出属性域清单 —— ArcGIS Pro 版

打印工作空间内所有属性域及其编码值/区间，是建立标准字典、检查值域合规性的基础。

参数顺序（按地理处理工具原定义）：
  1. 输入数据集（可多个）（Input Datasets）
  2. 输入工作空间（GDB / 文件夹 / SDE）（Workspace）

用法：
    python run.py <Input Datasets> <Workspace>
"""
# -*- coding: utf-8 -*-

import arcpy
import csv
import os


class ListAttDomains(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Domains"
        self.description = "Print out attribute domains"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_datasets = arcpy.Parameter(
            displayName="Input Datasets",
            name="in_datasets",
            datatype=["GPFeatureLayer", "DETable"],
            parameterType="Required",
            direction="Input",
            multiValue=True)

        in_ws = arcpy.Parameter(
            displayName="Workspace",
            name="in_ws",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        in_ws.filter.list = ['LocalDatabase', 'RemoteDatabase']

        parameters = [in_datasets, in_ws]

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
        input_datasets = parameters[0].valueAsText.split(';')
        wspace = parameters[1].valueAsText

        arcpy.env.workspace = wspace
        domaindicts = self.codeddomainDict(wspace)

        for counter, dataset in enumerate(input_datasets, start=1):
            dataset = dataset.replace("'", "")
            desc = arcpy.Describe(dataset)
            arcpy.AddMessage(("\n# {} of {} : {}".format(counter, len(
                input_datasets), desc.baseName)))

            fields = arcpy.ListFields(dataset)
            # dictionary - {field name lowercase: domain name lowercase}
            fieldswithdomain = {field.name.lower(): field.domain.lower()
                                for field in fields if
                                field.domain != ""}
            # all attribute elements
            for counter1, field in enumerate(fieldswithdomain):
                if counter1 > 0:
                    arcpy.AddMessage("  ")
                arcpy.AddMessage("    - field name : {}".format(field))
                arcpy.AddMessage("    - domain name: {}".format(
                    fieldswithdomain[field]))
                domaincodelist = domaindicts[fieldswithdomain[field]]
                for ecodeddomain in domaincodelist.keys():
                    arcpy.AddMessage(
                        "                 {} : {}".format(ecodeddomain,
                                                          domaincodelist[
                                                              ecodeddomain]))
        arcpy.AddMessage("  ")
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
    tools = ListAttDomains()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
