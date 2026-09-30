# -*- coding: utf-8 -*-
"""
加权合成评价指数 —— ArcGIS Pro 版

把多个已标准化的指标字段按权重加权合成为一个综合指数字段，用于适宜性评价、综合评分。

参数顺序（按工具原定义）：
  1. FeatureClass（FeatureClass）
  2. WeightTable（WeightTable）
  3. OutputFieldName（OutputFieldName）
  4. NullFillValue（NullFillValue）

用法：
    python run.py <FeatureClass> <WeightTable> <OutputFieldName> <NullFillValue>
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


# Name: ComputeWeightedIndex.py
# Purpose: This function will return a weighted index based on the input feature class and the input variable weight value table.
# Last Modified: 3/6/2025
# Python Version:   3.9
# ArcGIS Version: 3.2 Pro
# --------------------------------
#
#
#
# Unless required by applicable law or agreed to in writing, software
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# --------------------------------
import arcpy
import datetime
import numpy as np
import os
import pandas as pd
from scipy import stats

import SharedArcNumericalLib as san




def compute_weighted_index(
    in_fc,
    input_variable_weight_value_table,
    output_field_name="weighted_index",
    null_fill_value=0,
):
    """This function will return a weighted index based on the input feature class and the input variable weight value table.
    Parameters
    -----------------
    in_fc- input feature class that has scored variables to combine into a weighted index.
    input_variable_weight_value_table - table of input variables and their associated weights for the output weighted index.
    output_field_name - the name of the output field that will contain the weighted index.
    null_fill_value - the value to fill in for null values in the input variables.
    """
    try:
        arcpy.env.overwriteOutput = True
        desc = arcpy.Describe(in_fc)
        OIDFieldName = desc.OIDFieldName
        workspace = os.path.dirname(desc.catalogPath)
        san.arc_print("Converting table to dataframe...")

        # Convert value table to dictionary
        weight_dict = {}
        value_table = input_variable_weight_value_table
        for i in range(0, value_table.rowCount):
            var = value_table.getValue(i, 0)
            weight = float(value_table.getTrueValue(i, 1))
            weight_dict[var] = weight

        # Convert feature class to DataFrame
        columns = [i for i in weight_dict]
        df = san.arcgis_table_to_df(in_fc, columns)

        # Fill null values
        df.fillna(null_fill_value, inplace=True)

        # Calculate weighted index
        san.arc_print("Calculating weighted index...")
        for key in weight_dict:
            weight = weight_dict[key]
            if output_field_name in df.columns:
                df[output_field_name] = df[var].astype(float) * float(weight) + df[output_field_name]
            else:
                df[output_field_name] = df[var].astype(float) * float(weight)

        # Prepare for export
        JoinField = arcpy.ValidateFieldName("DFIndexJoin", workspace)
        df[JoinField] = df.index

        san.arc_print("Exporting dataframe to structured numpy array.", True)
        finalArray = df[[output_field_name, JoinField]].to_records(index=False)

        san.arc_print(f"Joining {output_field_name} to feature class.", True)
        arcpy.da.ExtendTable(
            in_fc, OIDFieldName, finalArray, JoinField, append_only=False
        )
        san.arc_print("Script Completed Successfully.", True)

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(str(e))

        # End do_analysis function


# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE,
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == "__main__":
    FeatureClass = _argv(0)
    WeightTable = _gp(1)
    OutputFieldName = _argv(2)
    NullFillValue = int(_gp(3))
    compute_weighted_index(FeatureClass, WeightTable, OutputFieldName, NullFillValue)
