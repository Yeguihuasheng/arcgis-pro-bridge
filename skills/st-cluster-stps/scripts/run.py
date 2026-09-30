# -*- coding: utf-8 -*-
"""
时空路径聚类 —— ArcGIS Pro 版

把带时间戳的点构建成时空路径（STPs）并做聚类，输出聚类结果与统计，用于活动模式分析、轨迹聚类。

参数顺序（按地理处理工具原定义）：
  1. Input STPs（Input STPs）
  2. Study Area（Study Area）
  3. Analysis Fields（Analysis Fields）
  4. Output Clusters（Output Clusters）

用法：
    python run.py <Input STPs> <Study Area> <Analysis Fields> <Output Clusters>
"""
# -*- coding: utf-8 -*-

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

import csv
import pandas as pd
from scipy.spatial.distance import euclidean

class STPs_to_Clusters(object):
    def __init__(self):
        self.label = "STPs to Clusters"
        self.description = "This tool takes STPs and analysis fields, and creates clusters of points derived from the raster of each of the analysis fields, based on Multi-Variate Clustering"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        stp_param = arcpy.Parameter(
            displayName = "Input STPs",
            name = "input_stps",
            datatype = "DEFeatureClass",
            parameterType = "Required",
            direction = "Input")

        study_area_param = arcpy.Parameter(
            displayName = "Study Area",
            name = "study_area",
            datatype = "DEFeatureClass",
            parameterType = "Required",
            direction = "Input")

        fields_param = arcpy.Parameter(
            displayName = "Analysis Fields",
            name = "analysis fields",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input",
            multiValue = True)

        clusters_param = arcpy.Parameter(
            displayName = "Output Clusters",
            name = "out_clusters",
            datatype = "DEFeatureClass",
            parameterType = "Required",
            direction = "Output")

        fields_param.parameterDependencies = [stp_param.name]
        params = [stp_param,study_area_param,fields_param,clusters_param]
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
        return

    def db_index(data):
        cluster_values = list(set([x['Cluster'] for x in data]))
        coord_count = len(data[0]['Value_Coordinates'])
        centroids = []
        for i in cluster_values:
            filtered_cluster = [x['Value_Coordinates'] for x in data if x['Cluster'] == i]
            total_coord = []
            for y in range(0, coord_count):
                total_coord.append(0)
            for item in filtered_cluster:
                for q in range(0, coord_count):
                    total_coord[q] += item[q]
            centroids_coord = []
            for value in total_coord:
                new_value = (value/float(len(filtered_cluster)))
                centroids_coord.append(new_value)
            new_dict = {'Cluster': i, 'Value_Coordinates': centroids_coord}
            centroids.append(new_dict)
        for value in data:
            cluster_value = value['Cluster']
            centroid_coord = [x['Value_Coordinates'] for x in centroids if x['Cluster'] == cluster_value]
            point_coord = value['Value_Coordinates']
            distance = float(euclidean(centroid_coord, point_coord))
            value['Centroid_Distance'] = distance
        for row in centroids:
            filtered_distance = [x['Centroid_Distance'] for x in data if x['Cluster'] == row['Cluster']]
            average_distance = sum(filtered_distance)/len(filtered_distance)
            row['Average_Distance'] = average_distance

        calculations_to_sum = []

        for first_cluster in centroids:
            compare = []
            for second_cluster in centroids:
                if first_cluster['Cluster'] != second_cluster['Cluster']:
                    cluster_distance = float(euclidean(first_cluster['Value_Coordinates'],
                                                       second_cluster['Value_Coordinates']))
                    solution = (first_cluster['Average_Distance']+second_cluster['Average_Distance'])/cluster_distance
                    compare.append(solution)
            calculations_to_sum.append(max(compare))

        cluster_calc_sum = sum(calculations_to_sum)

        db_score = ((1/len(cluster_values))*cluster_calc_sum)

        return db_score

    def execute(self, parameters, messages):
        stps = parameters[0].valueAsText
        study_area = parameters[1].valueAsText
        fields = parameters[2].valueAsText.split(";")
        out_clusters = parameters[3].valueAsText
        raster_list = []

        for field in fields:
            unclipped_raster = arcpy.sa.Spline(stps, field, spline_type='REGULARIZED')
            unsized_raster = arcpy.management.Clip(unclipped_raster,"#",f"{field}_unsized_raster",study_area,-1,"ClippingGeometry")
            raster = arcpy.management.Resample(unsized_raster, f"{field}", "20 20", "BILINEAR")
            raster_list.append(raster)
            arcpy.management.Delete(unclipped_raster)
            arcpy.management.Delete(unsized_raster)

        str_raster_list = []
        points_list = []

        for raster in raster_list:
            desc = arcpy.Describe(raster)
            str_raster = (f"{desc.name}")
            str_raster_list.append(str_raster)
            points_grid = arcpy.RasterToPoint_conversion(raster,f"{raster}_points","Value")
            points_list.append(points_grid)

        analysis_points = arcpy.CopyFeatures_management(points_list[0],"copy")
        arcpy.DeleteField_management(analysis_points,"grid_code")

        for item in str_raster_list:
            arcpy.AddField_management(analysis_points,item,"FLOAT")

        points_dict = {}

        for points in points_list:
            desc2 = arcpy.Describe(points)
            new_name = desc2.name.replace("_points","")
            with arcpy.da.SearchCursor(points, ["pointid", "grid_code"]) as find_val:
                id_list = []
                value_list = []
                for row in find_val:
                    id_list.append(row[0])
                    value_list.append(row[1])
                points_dict.update({"id": id_list, new_name: value_list})

        str_raster_list.insert(0, "pointid")

        with arcpy.da.UpdateCursor(analysis_points,str_raster_list) as give_val:
            for row in give_val:
                row_line = points_dict["id"].index(row[0])
                new_vals = []
                id_val = points_dict["id"][row_line]
                new_vals.append(id_val)
                for item in points_list:
                    desc3 = arcpy.Describe(item)
                    match_name = desc3.name.replace("_points", "")
                    val_val = points_dict[match_name][row_line]
                    new_vals.append(val_val)

                give_val.updateRow(new_vals)

        str_raster_list.remove("pointid")


        first_space_clusters = arcpy.SpatiallyConstrainedMultivariateClustering_stats(analysis_points, "unnumbered_clusters", str_raster_list, output_table="cluster_table")

        with arcpy.da.SearchCursor("cluster_table",["NUM_GROUPS","PSEUDO_F"]) as find_max:
            f_stat=[]
            for row in find_max:
                if 1 < row[0] < 6:
                    f_stat.append(row[1])

        best_val = max(f_stat)
        best_num = (f_stat.index(best_val))+2

        final_space_clusters = arcpy.SpatiallyConstrainedMultivariateClustering_stats(analysis_points, out_clusters, str_raster_list, number_of_clusters = best_num)

        stats=arcpy.GetMessages()

        messages.AddMessage(stats)

        str_raster_list.append('CLUSTER_ID')

        data = []

        with arcpy.da.SearchCursor(final_space_clusters, str_raster_list) as get_values:
            for thing in get_values:
                get_dict = {}
                get_dict["Cluster"] = thing[-1]
                get_dict["Value_Coordinates"] = thing[:-1]
                data.append(get_dict)

        cluster_values = list(set([x['Cluster'] for x in data]))
        coord_count = len(data[0]['Value_Coordinates'])
        centroids = []
        for i in cluster_values:
            filtered_cluster = [x['Value_Coordinates'] for x in data if x['Cluster'] == i]
            total_coord = []
            for y in range(0, coord_count):
                total_coord.append(0)
            for item in filtered_cluster:
                for q in range(0, coord_count):
                    total_coord[q] += item[q]
            centroids_coord = []
            for value in total_coord:
                new_value = (value/float(len(filtered_cluster)))
                centroids_coord.append(new_value)
            new_dict = {'Cluster': i, 'Value_Coordinates': centroids_coord}
            centroids.append(new_dict)
        for value in data:
            cluster_value = value['Cluster']
            centroid_coord = [x['Value_Coordinates'] for x in centroids if x['Cluster'] == cluster_value]
            point_coord = value['Value_Coordinates']
            distance = float(euclidean(centroid_coord, point_coord))
            value['Centroid_Distance'] = distance
        for row in centroids:
            filtered_distance = [x['Centroid_Distance'] for x in data if x['Cluster'] == row['Cluster']]
            average_distance = sum(filtered_distance)/len(filtered_distance)
            row['Average_Distance'] = average_distance

        calculations_to_sum = []

        for first_cluster in centroids:
            compare = []
            for second_cluster in centroids:
                if first_cluster['Cluster'] != second_cluster['Cluster']:
                    cluster_distance = float(euclidean(first_cluster['Value_Coordinates'],
                                                       second_cluster['Value_Coordinates']))
                    solution = (first_cluster['Average_Distance']+second_cluster['Average_Distance'])/cluster_distance
                    compare.append(solution)
            calculations_to_sum.append(max(compare))

        cluster_calc_sum = sum(calculations_to_sum)

        db_score = ((1/len(cluster_values))*cluster_calc_sum)

        messages.AddMessage(f"Davies Bouldin Score: {db_score}")

        arcpy.management.Delete(unclipped_raster)

        arcpy.management.Delete(first_space_clusters)

        arcpy.management.Delete(analysis_points)

        arcpy.management.Delete("cluster_table")

        for item in points_list:
            arcpy.management.Delete(item)


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
    tools = STPs_to_Clusters()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
