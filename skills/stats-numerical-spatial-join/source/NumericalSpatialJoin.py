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
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
    target_feature_class = arcpy.GetParameterAsText(0)
    join_feature_class = arcpy.GetParameterAsText(1)
    output_feature_Class = arcpy.GetParameterAsText(2)
    prepended_field_name = arcpy.GetParameterAsText(3)
    join_operation = arcpy.GetParameterAsText(4)
    join_type = "KEEP_ALL" if bool(arcpy.GetParameter(5)) else "KEEP_COMMON"
    match_option = str(arcpy.GetParameterAsText(6)).strip()
    search_radius = arcpy.GetParameter(7)
    # Simplify processing by associating input lists to target merge rules
    merge_rule_dict = {}
    merge_rule_identifiers = ["SUM", "MEAN", "MEDIAN", "MODE", "STD", "MIN", "MAX", "RANGE", "COUNT", "FIRST", "LAST"]
    for merge_rule, index in zip(merge_rule_identifiers, range(8, 19)):
        merge_rule_dict[merge_rule] = [field for field in _argv(index).split(";") if
                                       san.field_exist(join_feature_class, field)]
    statistical_spatial_join(target_feature_class, join_feature_class, output_feature_Class, prepended_field_name,
                             join_operation, join_type, match_option, search_radius, merge_rule_dict)
