# -*- coding: utf-8 -*-
"""
字段百分位评分 —— ArcGIS Pro 版

按指定字段的全域百分位给每个要素打分（0~100 或 0~1），用于等级划分、综合评级打分。

参数顺序（按工具原定义）：
  1. FeatureClass（FeatureClass）
  2. InputFields（InputFields）
  3. RankingGroupField（RankingGroupField）
  4. InvertRank（InvertRank）
  5. RankMethod（RankMethod）
  6. NullValueFill（NullValueFill）
  7. NumberRank（NumberRank）

用法：
    python run.py <FeatureClass> <InputFields> <RankingGroupField> <InvertRank> <RankMethod> <NullValueFill> <NumberRank>
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


# Name: PercentileScoreFields.py
# Purpose: Will add selected fields as percentile scores by extending a numpy array to the feature class.
# Last Modified: 5/29/2022
# Python Version:   2.7-3.1
# ArcGIS Version: 10.4 (Pro)
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




def add_percentile_fields(
    in_fc,
    input_fields,
    ranking_group_field=None,
    invert_score=False,
    percent_rank_method="average",
    null_fill_value=0,
    number_rank=False,
):
    """This function will take in a feature class, and use pandas/numpy to calculate percentile scores and then
    join them back to the feature class using arcpy.
    Parameters
    -----------------
    in_fc- input feature class to add percentile fields
    input_fields - table fields to percentile score
    ranking_group_field - this field will look at the unique values in a field and group the percentile scores so
        they are ranked relative to the values in each group.
    invert_score - boolean
        Will make lower values be scored as higher values
    percent_rank_method - {‘average’, ‘min’, ‘max’, ‘dense’, ‘ordinal’}, optional
        The method used to assign percentile ranks to tied elements.
        The following methods are available (default is ‘average’):
        ‘average’: The average of the ranks that would have been assigned to all the tied values is assigned to each
        value.
        ‘min’: The minimum of the ranks that would have been assigned to all the tied values is assigned to each value.
         (This is also referred to as “competition” ranking.)
        ‘max’: The maximum of the ranks that would have been assigned to all the tied values is assigned to each value.
        ‘dense’: Like ‘min’, but the rank of the next highest element is assigned the rank immediately after those
        assigned to the tied elements.
        ‘first’: Ranks assigned in order they appear in the array.
    na_fill - float
        Will fill null values with the chosen value. Defaults to 0.5
    number_rank - boolean
        Will rank the values as numbers instead of percent ranks. This will be a number between 1 and the number of
        values in the field.
    """
    try:
        arcpy.env.overwriteOutput = True
        desc = arcpy.Describe(in_fc)
        OIDFieldName = desc.OIDFieldName
        workspace = os.path.dirname(desc.catalogPath)
        san.arc_print("Converting table to dataframe...")
        relative_ranking = False
        scoring_fields = [i for i in input_fields]
        if san.field_exist(in_fc, ranking_group_field):
            san.arc_print("Using relative ranking for scoring...")
            input_fields.append(ranking_group_field)
            relative_ranking = True
        df = san.arcgis_table_to_df(in_fc, input_fields)
        san.arc_print("Adding Percentile Rank Scores...")
        ranking_group_field = ranking_group_field if relative_ranking else None
        pct_bool = not number_rank
        scored_df = san.generate_percentile_metric(
            df,
            scoring_fields,
            ranking_group_field,
            method=percent_rank_method,
            na_fill=null_fill_value,
            invert=invert_score,
            pct=pct_bool,
        )
        scored_df = scored_df.drop(columns=input_fields)
        JoinField = arcpy.ValidateFieldName("DFIndexJoin", workspace)
        scored_df[JoinField] = scored_df.index
        san.arc_print(
            "Exporting new percentile dataframe to structured numpy array.", True
        )
        finalStandardArray = scored_df.to_records()
        san.arc_print(
            "Joining new percent rank fields to feature class. The new fields are {0}".format(
                str(scored_df.columns)
            ),
            True,
        )
        san.arc_print(
            "Sample of new fields: {0}".format(str(scored_df.head().to_string()))
        )
        arcpy.da.ExtendTable(
            in_fc, OIDFieldName, finalStandardArray, JoinField, append_only=False
        )
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
    FeatureClass = _argv(0)
    InputFields = _argv(1).split(";")
    RankingGroupField = _argv(2)
    InvertRank = bool(_gp(3))
    RankMethod = _argv(4)
    NullValueFill = float(_argv(5))
    NumberRank = bool(_gp(6))
    add_percentile_fields(
        FeatureClass,
        InputFields,
        RankingGroupField,
        InvertRank,
        RankMethod,
        NullValueFill,
        NumberRank,
    )
