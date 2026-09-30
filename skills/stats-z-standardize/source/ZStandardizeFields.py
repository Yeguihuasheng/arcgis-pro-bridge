# Name: ZStandardizeFields.py
# Purpose: Will add selected fields as standardized Z scores by extending a numpy array to the feature class.
# Last Modified: 4/16/2021
# Python Version:   2.7-3.1
# ArcGIS Version: 10.4 (Pro)
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
import os, arcpy
import pandas as pd
import SharedArcNumericalLib as san




def add_standarized_fields(in_fc, input_Fields, ignore_nulls=True):
    """This function will take in a feature class, and use pandas/numpy to calculate Z-scores and then
    join them back to the feature class using arcpy.
        Parameters
    -----------------
    in_fc- input feature class to add Z-score fields
    input_fields - table fields to add Z scores to
    ignore_nulls - ignore null values in Z-score calculations"""
    try:
        arcpy.env.overwriteOutput = True
        desc = arcpy.Describe(in_fc)
        OIDFieldName = desc.OIDFieldName
        workspace = os.path.dirname(desc.catalogPath)
        input_Fields_List = input_Fields
        finalColumnList = []
        scored_df = None
        for column in input_Fields_List:
            try:
                field_series = san.arcgis_table_to_dataframe(
                    in_fc, [column], skip_nulls=ignore_nulls, null_values=0
                )
                san.arc_print(
                    "Creating standardized column for field {0}.".format(str(column)),
                    True,
                )
                col_Standarized = arcpy.ValidateFieldName("Zscore_" + column, workspace)
                field_series[col_Standarized] = (
                    field_series[column] - field_series[column].mean()
                ) / field_series[column].std(ddof=0)
                finalColumnList.append(col_Standarized)
                if col_Standarized != column:
                    del field_series[column]
                if scored_df is None:
                    san.arc_print("Test")
                    scored_df = field_series
                else:
                    scored_df = pd.merge(
                        scored_df,
                        field_series,
                        how="outer",
                        left_index=True,
                        right_index=True,
                    )
            except Exception as e:
                san.arc_print("Could not process field {0}".format(str(column)))
                san.arc_print(e.args[0])
                pass
        JoinField = arcpy.ValidateFieldName("DFIndexJoin", workspace)
        scored_df[JoinField] = scored_df.index
        finalColumnList.append(JoinField)
        san.arc_print(
            "Exporting new standardized dataframe to structured numpy array.", True
        )
        finalStandardArray = scored_df.to_records()
        san.arc_print(
            "Joining new standardized fields to feature class. The new fields are {0}".format(
                str(finalColumnList)
            ),
            True,
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
    FeatureClass = arcpy.GetParameterAsText(0)
    InputFields = arcpy.GetParameterAsText(1).split(";")
    IgnoreNulls = bool(arcpy.GetParameter(2))
    add_standarized_fields(FeatureClass, InputFields, IgnoreNulls)
