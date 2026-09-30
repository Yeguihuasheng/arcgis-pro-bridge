# -*- coding: utf-8 -*-
"""
核密度估值回写矢量 —— ArcGIS Pro 版

对点要素做核密度分析并把密度值提取回写（可沿网络），用于热度评估、密度图量化到单元。

参数顺序（按工具原定义）：
  1. input_feature_class（input_feature_class）
  2. weighted_fields（weighted_fields）
  3. input_network（input_network）
  4. percentile_bool（percentile_bool）
  5. field_edit（field_edit）
  6. cell_size（cell_size）
  7. search_radius（search_radius）
  8. area_unit_factor（area_unit_factor）
  9. percentage_sample（percentage_sample）
  10. group_by_stat（group_by_stat）
  11. barrier_fc（barrier_fc）
  12. intermediate_ra（intermediate_ra）

用法：
    python run.py <input_feature_class> <weighted_fields> <input_network> <percentile_bool> <field_edit> <cell_size> <search_radius> <area_unit_factor> <percentage_sample> <group_by_stat> <barrier_fc> <intermediate_ra>
"""

import os
import sys

import arcpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _argv(i):
    """替代 arcpy.GetParameterAsText(i)：从命令行取第 i 个参数（字符串）。"""
    if len(sys.argv) > i + 1:
        return sys.argv[i + 1]
    return u""


def _gp(i):
    """替代 arcpy.GetParameter(i)：按常见类型还原命令行参数（数值/布尔/字符串）。"""
    if len(sys.argv) <= i + 1:
        return None
    v = sys.argv[i + 1]
    if v == u"":
        return None
    low = v.lower()
    if low == u"true":
        return True
    if low == u"false":
        return False
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


# --------------------------------
# Name: DensityToVector.py
# Purpose: This script is intended to help aid the network/vector analysis process by computing weighted kernel densities on
# list of incoming fields which represent weights for the KDE estimation. These estimations are then joined back to
# a network feature class. If provided a list of numbers, the tool will compute percentiles of the input densities
# and will add percentile scores to the input densities for non-zero/non-null values.
# Current Owner: David Wasserman
# Last Modified: 1/25/2022
# ArcGIS Version:   ArcGIS Pro/10.4
# Python Version:   3.8/2.7
# --------------------------------
#
#
#
# Unless required by applicable law or agreed to in writing, software
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# --------------------------------

import arcpy
import numpy as np

import SharedArcNumericalLib as san

try:
    import pandas as pd
except:
    arcpy.AddError(
        "This library requires Pandas installed in the ArcGIS Python Install."
        " Might require installing pre-requisite libraries and software."
    )
try:
    arcpy.CheckExtension("Spatial")
except:
    arcpy.AddError("This tool requires spatial analyst to function. Please add SA.")




def density_to_vector(
    in_fc,
    weighted_fields,
    input_network,
    percentile_bool=True,
    field_edit="",
    cell_size=500,
    search_radius=800,
    area_unit="SQUARE_MILES",
    sample_percentage=25,
    group_by_statistic="median",
    barrier_fc="",
    intermediate_raster="",
):
    """This function will compute kernel densities and associate them with a target network/vector file. If the
    percentile bool is true, percentile scores are added along side each density.
    Parameters
    -----------------
    in_fc: input feature class
    weighted_fields: fields to use for a weighted KDE
    input_network: point,polyline,polygon file to associate density values to
    percentile_bool: if true, adds percentiles to scores
    field_edit: prepended field name
    cell_size: cell size of KDE raster
    search_radius: search radius/bandwidth of KDE
    area_unit: unit of output raster
    sample_percentage: determines the sample point density for polyline files. 10 will give 1 point every 10% of the line.
       Includes stop and end points.
    group_by_statistic: if multiple sample points are used, this is the statistic used to aggregate it, based
            on options accepted by agg function in pandas:
            https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.agg.html.
    barrier_fc: a feature class (line or polygon) that defines a barrier for KDE estimation.
    intermediate_raster: The output save location for intermediate raster files from the kernel density.
    """
    try:
        arcpy.env.overwriteOutput = True
        desc = arcpy.Describe(input_network)
        work_space = desc.catalogPath
        arcpy.env.scratchWorkspace = "memory"  # Scratch in memory
        arcpy.env.extent = input_network  # Set extent to input network, rather than default point extent
        temp_out_sample = "memory/sample_points_out"
        temp_sample_points = "memory/sample_points"
        temp_input_layer = "Temp_Input_Layer"
        join_field = "JNField"
        join_index = "JNindex"
        oid_field = str(desc.OIDFieldName)
        san.add_new_field(input_network, join_field, "LONG")
        arcpy.CalculateField_management(
            input_network, join_field, "!{0}!".format(oid_field), "PYTHON"
        )
        san.arc_print("Generating sample points from feature class in memory...")
        san.generate_sample_points(
            input_network, temp_sample_points, int(sample_percentage)
        )
        final_df = None
        for field in weighted_fields:
            san.arc_print("Computing density for field {0}...".format(field))
            arcpy.MakeFeatureLayer_management(
                in_fc,
                temp_input_layer,
                san.construct_sql_equality_query(
                    field, None, work_space, noneEqualityOperator="is not"
                ),
            )
            output_kde = arcpy.sa.KernelDensity(
                in_fc,
                str(field),
                cell_size,
                search_radius,
                area_unit,
                in_barriers=barrier_fc,
            )
            if intermediate_raster:
                san.arc_print("Generating an intermediate raster...")
                output_kde.save(intermediate_raster)
            arcpy.sa.ExtractValuesToPoints(
                temp_sample_points, output_kde, temp_out_sample, True
            )
            raw_sample_df = san.arcgis_table_to_df(
                temp_out_sample, [join_field, "RASTERVALU"]
            )
            new_field_name = "DN_" + str(field_edit) + str(field)
            raw_sample_df[new_field_name] = raw_sample_df["RASTERVALU"]
            raw_sample_df[new_field_name].fillna(0, inplace=True)
            raw_sample_df = raw_sample_df.groupby(join_field).agg(
                str(group_by_statistic).lower()
            )
            if percentile_bool:
                new_percentile_field = "Per_" + str(field_edit) + str(field)
                raw_sample_df[new_percentile_field] = raw_sample_df[
                    new_field_name
                ].rank(pct=True)
            field_list = (
                [new_field_name, new_percentile_field]
                if percentile_bool
                else [new_field_name]
            )
            if final_df is not None:
                final_df = pd.concat([final_df, raw_sample_df[field_list]], axis=1)
            else:
                raw_sample_df[join_index] = raw_sample_df.index
                final_df = raw_sample_df[[join_index] + field_list]
        final_df.reset_index()
        san.arc_print("Extending density fields to table...")
        final_df = san.validate_df_names(final_df, work_space)
        fin_records = final_df.to_records()
        arcpy.da.ExtendTable(
            input_network, join_field, fin_records, join_index, append_only=False
        )
        san.arc_print("Deleting temporary join field...")
        arcpy.DeleteField_management(input_network, [join_field, join_index])
        san.arc_print("Script Completed Successfully.", True)

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


# End do_analysis function

# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE,
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == "__main__":
    # Define input parameters
    input_feature_class = _argv(0)
    weighted_fields = _gp(1)
    input_network = _argv(2)
    percentile_bool = _gp(3)
    field_edit = _argv(4)
    cell_size = _gp(5)
    search_radius = _gp(6)
    area_unit_factor = _gp(7)
    percentage_sample = _gp(8)
    group_by_stat = _gp(9)
    barrier_fc = _argv(10)
    intermediate_ra = _argv(11)
    density_to_vector(
        input_feature_class,
        weighted_fields,
        input_network,
        bool(percentile_bool),
        field_edit,
        cell_size,
        search_radius,
        area_unit_factor,
        percentage_sample,
        group_by_stat,
        barrier_fc,
        intermediate_ra,
    )
