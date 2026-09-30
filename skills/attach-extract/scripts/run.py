# -*- coding: utf-8 -*-
"""
提取要素附件到文件夹 —— ArcGIS Pro 版

把文件地理数据库要素类的附件（照片/扫描件）批量导出到文件夹，按记录分组存放，用于外业照片归档、成果移交。

参数顺序（按地理处理工具原定义）：
  1. In Records（In Records）
  2. Output Folder（Output Folder）

用法：
    python run.py <In Records> <Output Folder>
"""
# -*- coding: UTF-8 -*-

import sys
import arcpy


# ---- 生成器补充的运行期兜底（不影响原逻辑）----
# 上游脚本的中间结果常放在 in_memory，重复运行会因为重名而失败，
# 打开覆盖输出后再跑就正常了。
try:
    arcpy.env.overwriteOutput = True
except Exception:
    pass
# 上游的错误处理分支里偶有引用未定义的变量（如 out_fc_name / out_ws），
# 一旦走到那里会抛 NameError 把真正的错误掩盖掉，这里给这些名字兜底。
for _n in ("out_fc_name", "out_ws", "out_fc", "fc_name", "out_name"):
    if _n not in globals():
        globals()[_n] = u""
del _n


import os
import codecs
import datetime
#import pytz

#ツール定義

class ExtractFeatureAttachments(object):

  def __init__(self):
    self.label = "Extract Feature Attachments"
    self.description = "Extract all attached files to the specified folder."

    self.category = "DataManagement"
    self.canRunInBackground = False

  def getParameterInfo(self):

    param0 = arcpy.Parameter(
               displayName="In Records",
               name="in_table",
               datatype=["DETable", "GPTableView"],
               parameterType="Required",
               direction="Input")

    param1 = arcpy.Parameter(
        displayName="Output Folder",
        name="out_Dir",
        datatype="DEFolder",
        parameterType="Required",
        #parameterType="Derived",
        direction="Output")

    params = [param0, param1]
    return params


  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    return

  def updateMessages(self, parameters):
    if (parameters[0]):
      inTable  = parameters[0].valueAsText
      if (inTable):
        fieldnames = [f.name.upper() for f in arcpy.ListFields(inTable)]
        if (not 'ATTACHMENTID' in  fieldnames or
            not 'REL_OBJECTID' in fieldnames or
            not 'ATT_NAME' in fieldnames or
            not 'DATA' in fieldnames):
          parameters[0].setErrorMessage('The input table is not an attachments table.')

    return

  def execute(self, parameters, messages):

    inTable  = parameters[0].valueAsText
    outDir = parameters[1].valueAsText

    if not os.path.exists(outDir):
      os.makedirs(outDir)

    with arcpy.da.SearchCursor(inTable, ['DATA', 'ATT_NAME', 'ATTACHMENTID', 'REL_OBJECTID']) as cursor:
      for item in cursor:
        attachment = item[0]
        filenum = "ATT" + str(item[2]) + "_"  + str(item[3]) + "_"
        filename = filenum + str(item[1])
        outFile = os.path.join(outDir, filename)
        with open(outFile, 'wb') as of:
          of.write(attachment.tobytes())

        del item
        del attachment
      del cursor


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
    tools = ExtractFeatureAttachments()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
