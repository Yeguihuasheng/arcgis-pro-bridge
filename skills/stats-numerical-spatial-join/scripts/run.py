# -*- coding: utf-8 -*-
"""
数值汇总空间连接 —— ArcGIS Pro 版

把连接要素的数值字段按空间关系汇总（求和/均值/中位数/众数/标准差/最小/最大/极差/计数等）写到目标要素上，字段名可加前缀，用于按单元汇总 POI 数、人口数。

参数顺序（按工具原定义）：
  1. target_feature_class（target_feature_class）
  2. join_feature_class（join_feature_class）
  3. output_feature_Class（output_feature_Class）
  4. prepended_field_name（prepended_field_name）
  5. join_operation（join_operation）
  6. param5（param5）
  7. match_option（match_option）
  8. search_radius（search_radius）

用法：
    python run.py <target_feature_class> <join_feature_class> <output_feature_Class> <prepended_field_name> <join_operation> <param5> <match_option> <search_radius>
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
# Name: NumericalSpatialJoin.py
# Purpose: This script is intended to provide an alternative method and GUI for spatial joins so that target feature
# classes are set to first and additional join fields are chosen by statistic. A field is provided to change the name.
# Current Owner: David Wasserman
# Last Modified: 2/7/2021
# ArcGIS Version:   ArcGIS Pro/10.4
# Python Version:   3.5/2.7
# --------------------------------
#
#
#
# Unless required by applicable law or agreed to in writing, software
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# --------------------------------

import arcpy
import SharedArcNumericalLib as san



def statistical_spatial_join(target_feature, join_features, out_feature_class, prepended_field_name="",
                             join_operation="JOIN_ONE_TO_ONE", join_type=True, match_option="INTERSECT",
                             search_radius=None, merge_rule_dict={}):
    """This function will join features to a target feature class using merge fields that are chosen based on the
     chosen summary statistics fields from the join feature class while keeping all the fields in the target.
     Parameters
    -----------------
    target_feature - Attributes of the target features and the attributes from the joined features are transferred to
    the output feature class. However, a subset of attributes can be defined in the field map parameter.
    join_features - The attributes from the join features are joined to the attributes of the target features.
    See the explanation of the join_operation parameter for details on how the aggregation of joined attributes
    are affected by the type of join operation.
    out_feature_class - A new feature class containing the attributes of the target and join features. By default,
    all attributes of target features and the attributes of the joined features are written to the output. However,
    the set of attributes to be transferred can be controlled by the field map parameter.
    join_operation - Specifies how joins between the target features and join features will be handled in the output
    feature class if multiple join features are found that have the same spatial relationship with a single target
    feature.
        JOIN_ONE_TO_ONE —If multiple join features are found that have the same spatial relationship with a single
         target feature, the attributes from the multiple join features will be aggregated using a field map merge rule.
         For example, if a point target feature is found within two separate polygon join features, the attributes from
          the two polygons will be aggregated before being transferred to the output point feature class. If one polygon
          has an attribute value of 3 and the other has a value of 7, and a Sum merge rule is specified, the aggregated
          value in the output feature class will be 10. This is the default.
        JOIN_ONE_TO_MANY —If multiple join features are found that have the same spatial relationship with a single
         target feature, the output feature class will contain multiple copies (records) of the target feature. For
         example, if a single point target feature is found within two separate polygon join features, the output
         feature class will contain two copies of the target feature: one record with the attributes of one polygon
         and another record with the attributes of the other polygon.
     join_type - Specifies whether all target features will be maintained in the output feature class (known as outer
      join) or only those that have the specified spatial relationship with the join features (inner join).
        KEEP_ALL —All target features will be maintained in the output (outer join). This is the default.
        KEEP_COMMON — Only those target features that have the specified spatial relationship with the join features
         will be maintained in the output feature class (inner join). For example, if a point feature class is specified
         for the target features, and a polygon feature class is specified for the join features, with match_option =
          "WITHIN", the output feature class will only contain those target features that are within a polygon
          join feature. Any target features not within a join feature will be excluded from the output.
      match_option - Specifies the criteria used to match rows.
        See https://pro.arcgis.com/en/pro-app/latest/tool-reference/analysis/spatial-join.htm
     search_radius - Join features within this distance of a target feature will be considered for the spatial join.
     merge_rule_dict - a dictionary of the form {statistic_type:[Fields,To,Summarize]}
     """
    try:
        arcpy.env.overwriteOutput = True
        san.arc_print("Generating fieldmapping...")
        f_map = san.generate_statistical_fieldmap(target_feature, join_features, prepended_field_name, merge_rule_dict)
        san.arc_print("Conducting spatial join...")
        arcpy.SpatialJoin_analysis(target_features=target_feature, join_features=join_features,
                                   out_feature_class=out_feature_class, join_operation=join_operation,
                                   join_type=join_type, match_option=match_option, search_radius=search_radius
                                   , field_mapping=f_map)
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
if __name__ == '__main__':
    # Define input parameters
    target_feature_class = _argv(0)
    join_feature_class = _argv(1)
    output_feature_Class = _argv(2)
    prepended_field_name = _argv(3)
    join_operation = _argv(4)
    join_type = "KEEP_ALL" if bool(_gp(5)) else "KEEP_COMMON"
    match_option = str(_argv(6)).strip()
    search_radius = _gp(7)
    # Simplify processing by associating input lists to target merge rules
    merge_rule_dict = {}
    merge_rule_identifiers = ["SUM", "MEAN", "MEDIAN", "MODE", "STD", "MIN", "MAX", "RANGE", "COUNT", "FIRST", "LAST"]
    for merge_rule, index in zip(merge_rule_identifiers, range(8, 19)):
        merge_rule_dict[merge_rule] = [field for field in _argv(index).split(";") if
                                       san.field_exist(join_feature_class, field)]
    statistical_spatial_join(target_feature_class, join_feature_class, output_feature_Class, prepended_field_name,
                             join_operation, join_type, match_option, search_radius, merge_rule_dict)
