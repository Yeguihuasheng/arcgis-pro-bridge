# -*- coding: utf-8 -*-
"""
按夹角最近空间连接线 —— ArcGIS Pro 版

在搜索半径内为目标线找方向夹角最接近的连接线并做一对一空间连接，用于路网接驳、等高线接边、管线顺接。

参数顺序（按地理处理工具原定义）：
  1. Target Lines（Target Lines）
  2. Join Lines（Join Lines）
  3. 输入工作空间（GDB / 文件夹 / SDE）（Workspace）
  4. Output Lines（Output Lines）
  5. Search Radius（Search Radius）
  6. Overwrite Output（Overwrite Output）

用法：
    python run.py <Target Lines> <Join Lines> <Workspace> <Output Lines> <Search Radius> <Overwrite Output>
"""
"""
Spatial Angle Join

Spatially join line features (one to one) within a radius that have the most similar
polar angle.

ArcGIS License: Basic

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

import numpy as np
import os

def spatial_angle_join(target, join, out_features, search_radius):
        operation = "JOIN_ONE_TO_MANY"
        match = "WITHIN_A_DISTANCE"

        output = r"in_memory/output"
        
        join_angles = angle_lookup(join)
        target_angles = angle_lookup(target)
        
        arcpy.SpatialJoin_analysis(target, 
                join, 
                output, 
                join_operation=operation, 
                match_option=match,
                search_radius=search_radius)
        
        acute_angles = find_acute_angles(output, target_angles, join_angles)
        
        save_join_with_similar_angle(acute_angles, output)
        
        arcpy.CopyFeatures_management(output, out_features)
def get_angle(line):
        p1 = line.firstPoint
        p2 = line.lastPoint
        y = p1.Y-p2.Y
        x = p1.X-p2.X
        if x == 0:
                if y > 0:
                        angle = np.pi/2
                else:
                        angle = (-1)*np.pi/2
        else:
                angle = np.arctan(y/x)
        angle = np.degrees(angle)
        return angle
def get_acute_angle(a1, a2):
        angle = np.abs( a1 - a2 )
        if angle > 90:
                angle = 180 - angle
        return angle
def angle_lookup(features):
        angle_lookup = dict()
        with arcpy.da.SearchCursor(features,["OID@","SHAPE@"]) as cur:
                for row in cur:
                        angle_lookup[row[0]] = get_angle(row[1])
        return angle_lookup
def find_acute_angles(output, target_angles, join_angles):
        acute_angles = list()
        with arcpy.da.SearchCursor(output, ["OID@","TARGET_FID","JOIN_FID"]) as cur:
                for row in cur:
                        oid = row[0]
                        tid = row[1]
                        jid = row[2]
                        if jid != -1:
                                target_angle = target_angles[tid]
                                join_angle = join_angles[jid]
                                acute_angle = get_acute_angle(target_angle, join_angle)
                                acute_angles.append((oid, tid, acute_angle))
                        else:
                                acute_angles.append((oid, tid, 0))
        return acute_angles
def save_join_with_similar_angle(acute_angles, output):
        acute_angles.sort(key=lambda d: d[2])
        save = set()
        trash = set()
        for delta in acute_angles:
                oid = delta[0]
                tid = delta[1]
                if tid in save:
                        trash.add(oid)
                else:
                        save.add(tid)
                        
        with arcpy.da.UpdateCursor(output, ["OID@"]) as cur:
                for row in cur:
                        if row[0] in trash:
                                cur.deleteRow()
class Join(object):
        def __init__(self):
                """Define the tool (tool name is the name of the class)."""
                self.label = "Join"
                self.description = ""
                self.canRunInBackground = False

        def getParameterInfo(self):
                """Define parameter definitions"""
                param0 = arcpy.Parameter(name = "target_lines",
                                         displayName = "Target Lines",
                                         direction = "Input",
                                         parameterType = "Required",
                                         datatype = "DEFeatureClass")
                param1 = arcpy.Parameter(name = "join_lines",
                                         displayName = "Join Lines",
                                         direction = "Input",
                                         parameterType = "Required",
                                         datatype = "DEFeatureClass")
                param2 = arcpy.Parameter(name = "workspace",
                                         displayName = "Workspace",
                                         direction = "Input",
                                         parameterType = "Required",
                                         datatype = "DEWorkspace")
                param3 = arcpy.Parameter(name = "out_lines",
                                         displayName = "Output Lines",
                                         direction = "Input",
                                         parameterType = "Required",
                                         datatype = "GPString")
                param4 = arcpy.Parameter(name = "search_radius",
                                         displayName = "Search Radius",
                                         direction = "Input",
                                         parameterType = "Required",
                                         datatype = "GPLong")
                param5 = arcpy.Parameter(name="overwrite_output",
                                         displayName="Overwrite Output",
                                         direction="Input",
                                         parameterType="Required",
                                         datatype="GPBoolean")
                param5.value = True

                params = [param0, param1, param2, param3, param4, param5]
                return params

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
                parameter.	This method is called after internal validation."""
                return

        def execute(self, parameters, messages):
                """The source code of the tool."""
                target = parameters[0].valueAsText
                join_lines = parameters[1].valueAsText
                workspace = parameters[2].valueAsText
                out_feature = parameters[3].valueAsText

                out_lines = os.path.join(workspace, out_feature)

                radius = parameters[4].value
                arcpy.env.overwriteOutput = parameters[5].value

                spatial_angle_join(target, join_lines, out_lines, radius)

                return




def spatial_angle_join(target, join, out_features, search_radius):
        operation = "JOIN_ONE_TO_MANY"
        match = "WITHIN_A_DISTANCE"

        output = r"in_memory/output"

        join_angles = angle_lookup(join)
        target_angles = angle_lookup(target)

        arcpy.SpatialJoin_analysis(target,
                join,
                output,
                join_operation=operation,
                match_option=match,
                search_radius=search_radius)

        acute_angles = find_acute_angles(output, target_angles, join_angles)

        save_join_with_similar_angle(acute_angles, output)

        arcpy.CopyFeatures_management(output, out_features)


def get_angle(line):
        p1 = line.firstPoint
        p2 = line.lastPoint
        y = p1.Y-p2.Y
        x = p1.X-p2.X
        if x == 0:
                if y > 0:
                        angle = np.pi/2
                else:
                        angle = (-1)*np.pi/2
        else:
                angle = np.arctan(y/x)
        angle = np.degrees(angle)
        return angle

def get_acute_angle(a1, a2):
        angle = np.abs( a1 - a2 )
        if angle > 90:
                angle = 180 - angle
        return angle


def angle_lookup(features):
        angle_lookup = dict()
        with arcpy.da.SearchCursor(features,["OID@","SHAPE@"]) as cur:
                for row in cur:
                        angle_lookup[row[0]] = get_angle(row[1])
        return angle_lookup

def find_acute_angles(output, target_angles, join_angles):
        acute_angles = list()
        with arcpy.da.SearchCursor(output, ["OID@","TARGET_FID","JOIN_FID"]) as cur:
                for row in cur:
                        oid = row[0]
                        tid = row[1]
                        jid = row[2]
                        if jid != -1:
                                target_angle = target_angles[tid]
                                join_angle = join_angles[jid]
                                acute_angle = get_acute_angle(target_angle, join_angle)
                                acute_angles.append((oid, tid, acute_angle))
                        else:
                                acute_angles.append((oid, tid, 0))
        return acute_angles



def save_join_with_similar_angle(acute_angles, output):
        acute_angles.sort(key=lambda d: d[2])
        save = set()
        trash = set()
        for delta in acute_angles:
                oid = delta[0]
                tid = delta[1]
                if tid in save:
                        trash.add(oid)
                else:
                        save.add(tid)

        with arcpy.da.UpdateCursor(output, ["OID@"]) as cur:
                for row in cur:
                        if row[0] in trash:
                                cur.deleteRow()

if __name__ == "__main__":
        main()


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
    tools = Join()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
