# -*- coding: utf-8 -*-
"""
查找并生成质心点 —— ArcGIS Pro 版

按分组条件为面要素求质心并生成点要素，可控制是否只保留落在面内的点，用于标注点与抽样点批量生成。

参数顺序（按地理处理工具原定义）：
  1. Polygon Feature Class（Polygon Feature Class）
  2. Group Field（Group Field）
  3. Ignore Null Values（Ignore Null Values）
  4. Project to WGS 1984（Project to WGS 1984）
  5. Output Point Feature Class（Output Point Feature Class）

用法：
    python run.py <Polygon Feature Class> <Group Field> <Ignore Null Values> <Project to WGS 1984> <Output Point Feature Class>
"""
# -*- coding: utf-8 -*-

"""
Finds centroids from polygons grouped by a field.

Copyright (c) 2023 Dalhousie University

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import sys
import arcpy, arcpy.da, arcpy.management


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


from collections.abc import Generator
from typing import List

import uuid
from contextlib import contextmanager

from pathlib import Path


# use_memory is copied from aputil.use_memory context manager
@contextmanager
def use_memory() -> Generator[str, None, None]:

    name = rf"memory\fc_{uuid.uuid4().hex}"

    try:
        yield name
    finally:
        arcpy.management.Delete(name)

class FindCentroidsTool(object):

    def __init__(self):

        self.label = "Find Centroids"
        self.description = "Finds centroids from polygons grouped by a field."
        self.canRunInBackground = False

    def getParameterInfo(self) -> List[arcpy.Parameter]:

        input_feature_class = arcpy.Parameter(
            name="input_feature_class",
            displayName="Polygon Feature Class",
            datatype="DEFeatureClass",
            direction="Input",
            parameterType="Required",
        )

        input_feature_class.filter.list = ["Polygon"]

        input_feature_class_field = arcpy.Parameter(
            name="group_field",
            displayName="Group Field",
            datatype="Field",
            direction="Input",
            parameterType="Required",
        )

        input_feature_class_field.parameterDependencies = [input_feature_class.name]

        ignore_null_values = arcpy.Parameter(
            name="ignore_null_values",
            displayName="Ignore Null Values",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Required",
        )

        ignore_null_values.value = True

        project_to_wgs84 = arcpy.Parameter(
            name="project_to_wgs84",
            displayName="Project to WGS 1984",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Required",
        )

        project_to_wgs84.value = True

        output_feature_class = arcpy.Parameter(
            name="output_feature_class",
            displayName="Output Point Feature Class",
            datatype="DEFeatureClass",
            direction="Output",
            parameterType="Required",
        )

        return [input_feature_class, input_feature_class_field, ignore_null_values, project_to_wgs84, output_feature_class]

    def isLicensed(self):
        return True

    def updateParameters(self, _):
        pass

    def updateMessages(self, _):
        pass

    def execute(self, parameters: List[arcpy.Parameter], _):

        params = {p.name: p for p in parameters}

        for p in parameters: p.clearMessage()

        input_feature_class = params.get("input_feature_class").valueAsText
        group_field = params.get("group_field").valueAsText
        output_feature_class = params.get("output_feature_class").valueAsText
        ignore_null_values: bool = params.get("ignore_null_values").value
        project_to_wgs84: bool = params.get("project_to_wgs84").value

        output_name = Path(output_feature_class).name
        output_path = str(Path(output_feature_class).parent)

        if not project_to_wgs84:
            spatial_reference = arcpy.Describe(input_feature_class).spatialReference
        else:
            spatial_reference = arcpy.SpatialReference(4326)

        arcpy.management.CreateFeatureclass(output_path, output_name, "Point", spatial_reference=spatial_reference)
        template_field: arcpy.Field = arcpy.ListFields(input_feature_class, group_field)[0]

        arcpy.management.AddField(
            output_feature_class,
            template_field.name,
            template_field.type,
            template_field.precision,
            template_field.scale,
            template_field.length,
            template_field.aliasName,
            template_field.isNullable,
            True,
            template_field.domain
        )

        with arcpy.da.SearchCursor(input_feature_class, [group_field]) as cursor:
            unique_values = set(record[0] for record in cursor if record[0] or not ignore_null_values)

        with arcpy.da.InsertCursor(output_feature_class, ["SHAPE@", group_field]) as input_cursor:

            for value in unique_values:

                field = arcpy.AddFieldDelimiters(input_feature_class, group_field)

                with use_memory() as selection, use_memory() as convex_hull:

                    if value:

                        if isinstance(value, (float, int, bool)):
                            where_clause = f"{field} = {value}"
                        else:
                            where_clause = f"{field} = '{value}'"

                    elif not ignore_null_values:

                        where_clause = f"{field} IS Null"

                    else:
                        continue

                    arcpy.AddMessage(f"Create Centroids for `{where_clause}`")

                    arcpy.management.MakeFeatureLayer(input_feature_class, selection, where_clause)
                    arcpy.management.MinimumBoundingGeometry(selection, convex_hull, "CONVEX_HULL", "ALL")

                    with arcpy.da.SearchCursor(convex_hull, "SHAPE@") as cursor:

                        polygon: arcpy.Polygon = next(cursor)[0]

                        if not project_to_wgs84:
                            centroid: arcpy.Point = polygon.trueCentroid
                        else:
                            centroid: arcpy.Point = polygon.projectAs("WGS 1984").trueCentroid

                        input_cursor.insertRow([centroid, value])

        return output_feature_class

    def postExecute(self, _):
        pass


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
    tools = FindCentroidsTool()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
