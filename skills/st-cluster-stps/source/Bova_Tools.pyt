# -*- coding: utf-8 -*-

import arcpy
import csv
import pandas as pd
from scipy.spatial.distance import euclidean

class Toolbox(object):
    def __init__(self):
        self.label = "Bova_Tools"
        self.alias = ""

        self.tools = [STPs_to_Clusters]


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
