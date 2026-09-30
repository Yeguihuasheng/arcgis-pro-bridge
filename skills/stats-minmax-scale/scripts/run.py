# -*- coding: utf-8 -*-
"""
字段极差归一化 —— ArcGIS Pro 版

对要素类的指定数值字段做 Min-Max 归一化（0~1），结果写入新字段，用于多指标评价前的量纲统一。

参数顺序（按工具原定义）：
  1. FeatureClass（FeatureClass）
  2. InputFields（InputFields）
  3. MinPercentile（MinPercentile）
  4. MaxPercentile（MaxPercentile）
  5. TargetMin（TargetMin）
  6. TargetMax（TargetMax）

用法：
    python run.py <FeatureClass> <InputFields> <MinPercentile> <MaxPercentile> <TargetMin> <TargetMax>
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


# Name: MinMaxScalingFields.py
# Purpose: Adds selected fields after applying min-max scaling by extending a numpy array to the feature class.
# The percentile options can be used to adjust what is considered the minimum
# or maximum based on a percentile scoring.
# AI Assistant: ChatGPT 4 (10/13/2023)
# Last Modified: 10/15/2023
# Python Version: 3.x
# ArcGIS Version: 10.4 (Pro)
# --------------------------------
import arcpy
import numpy as np
import os
import pandas as pd
import SharedArcNumericalLib as san


def add_min_max_scaled_fields(
    in_fc,
    input_fields,
    min_percentile=None,
    max_percentile=None,
    target_min=1,
    target_max=10,
):
    """
    This function takes an input feature class and fields, performs min-max scaling on the fields,
    and adds them back to the feature class. The percentile options can be used to adjust what is considered the minimum
    or maximum based on a percentile scoring.
    Parameters
    ----------
    in_fc: str
        This is the selected input feature class that will have new fields linearly normalized scores will be joined to it.
        If the fields already exist, they will be updated by the tool.
    input_fields: list
        List of fields to be scaled between either the min-max or some percentile band.
    min_percentile: float, optional
        Minimum percentile for scaling. Replaces the minimum.
    max_percentile: float, optional
        Maximum percentile for scaling. Replaces the maximum.
    target_min: float
        Minimum value of the target range for scaling.
    target_max: float
        Maximum value of the target range for scaling.
    """
    try:
        arcpy.env.overwriteOutput = True
        desc = arcpy.Describe(in_fc)
        OIDFieldName = desc.OIDFieldName
        workspace = os.path.dirname(desc.catalogPath)
        san.arc_print("Converting table to dataframe...", True)
        df = san.arcgis_table_to_df(in_fc, input_fields)
        san.arc_print("Adding Min-Max Scaled Scores...")
        if min_percentile is not None or max_percentile is not None:
            san.arc_print(
                "Using percentile scoring to determine either the min or the max...",
                True,
            )
        for field in input_fields:
            min_val = (
                np.percentile(df[field], min_percentile)
                if min_percentile is not None
                else df[field].min()
            )
            max_val = (
                np.percentile(df[field], max_percentile)
                if max_percentile is not None
                else df[field].max()
            )
            df[f"{field}_SCALED"] = target_min + (df[field] - min_val) * (
                target_max - target_min
            ) / (max_val - min_val)
            df[f"{field}_SCALED"] = df[f"{field}_SCALED"].clip(target_min, target_max)

        df.drop(columns=input_fields, inplace=True)
        join_field = arcpy.ValidateFieldName("DFIndexJoin", workspace)
        df[join_field] = df.index
        san.arc_print("Exporting new scored dataframe to structured numpy array.", True)

        final_scaled_array = df.to_records()
        san.arc_print(
            "Joining new percent rank fields to feature class. The new fields are {0}".format(
                str(df.columns)
            ),
            True,
        )
        arcpy.da.ExtendTable(
            in_fc, OIDFieldName, final_scaled_array, join_field, append_only=False
        )
        san.arc_print("Script completed successfully.", True)

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(str(e))


# Main function
if __name__ == "__main__":
    FeatureClass = _argv(0)
    InputFields = _argv(1).split(";")
    MinPercentile = (
        float(_argv(2))
        if _argv(2) != ""
        else None
    )
    MaxPercentile = (
        float(_argv(3))
        if _argv(3) != ""
        else None
    )
    TargetMin = (
        float(_argv(4)) if _argv(4) != "" else 0
    )
    TargetMax = (
        float(_argv(5)) if _argv(5) != "" else 1
    )
    add_min_max_scaled_fields(
        FeatureClass, InputFields, MinPercentile, MaxPercentile, TargetMin, TargetMax
    )
