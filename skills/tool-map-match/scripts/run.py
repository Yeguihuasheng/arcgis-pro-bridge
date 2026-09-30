# -*- coding: utf-8 -*-
"""
轨迹点地图匹配 —— ArcGIS Pro 版

把 GPS 轨迹点匹配吸附到道路网络线上，输出匹配后的轨迹，用于外业轨迹纠偏、路径还原。

参数顺序（按地理处理工具原定义）：
  1. Input track (shp)（Input track (shp)）
  2. Input road network (shp)（Input road network (shp)）
  3. Decay constant on network (in meter)（Decay constant on network (in meter)）
  4. Decay constant for Eucl. distances (in meter)（Decay constant for Eucl. distances (in meter)）
  5. maximum Eucl. distance for selecting segment candidates (in meter)（maximum Eucl. distance for selecting segment candidates (in meter)）
  6. Output Features（Output Features）

用法：
    python run.py <Input track (shp)> <Input road network (shp)> <Decay constant on network (in meter)> <Decay constant for Eucl. distances (in meter)> <maximum Eucl. distance for selecting segment candidates (in meter)> <Output Features>
"""

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

from mapmatcher import mapmatcher

class mapMatch(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "mapMatch"
        self.description = ""
        '''This tool allows map matching (matching of track points to a network)
        in arcpy using a Hidden Markov model with
               probabilities parameterized based on spatial + network distances.
               Follows the ideas in Newson, Krumm (2009):
               "Hidden markov Map Matching through noise and sparseness"
               '''
        self.canRunInBackground = False

    def getParameterInfo(self):
        #Define parameter definitions

        # Input Features parameter
        in_track = arcpy.Parameter(
            displayName="Input track (shp)",
            name="in_track",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Input")

        #in_track.filter.type = 'FeatureClass'
        #in_track.filter.list = ["Point"]

        # Input Features parameter
        in_roads = arcpy.Parameter(
            displayName="Input road network (shp)",
            name="in_roads",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Input")

        #in_roads.filter.type = 'FeatureClass'
       # in_roads.filter.list = ["Polyline"]

        # parameter 1
        decayconstantNet = arcpy.Parameter(
            displayName="Decay constant on network (in meter)",
            name="decayconstantNet",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")

        decayconstantNet.value = "30"

        # parameter 2
        decayConstantEu = arcpy.Parameter(
            displayName="Decay constant for Eucl. distances (in meter)",
            name="decayconstantEu",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")

        decayConstantEu.value = "10"

        # parameter 2
        maxDist = arcpy.Parameter(
            displayName="maximum Eucl. distance for selecting segment candidates (in meter)",
            name="maxDist",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")

        maxDist.value = "50"

##        # Derived Output Features parameter
##        out_features = arcpy.Parameter(
##            displayName="Output Features",
##            name="out_features",
##            datatype="GPFeatureLayer",
##            parameterType="Derived",
##            direction="Output")

        #out_features.parameterDependencies = [in_features.name]
        #out_features.schema.clone = True

        parameters = [in_track, in_roads, decayconstantNet, decayConstantEu, maxDist]

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

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_track  = parameters[0].valueAsText
        in_roads   = parameters[1].valueAsText
        decayconstantNet = parameters[2].valueAsText
        decayConstantEu = parameters[3].valueAsText
        maxDist = parameters[4].valueAsText

        opt = mapmatcher.mapMatch(in_track, in_roads,  decayconstantNet, decayConstantEu,maxDist)
        mapmatcher.exportPath(opt, in_track)


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
    tools = mapMatch()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
