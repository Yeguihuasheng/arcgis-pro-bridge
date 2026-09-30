"""


Create Date: Fri Sep 11 14:54:03 2019

Notice: Calculate Flood Inundation from DEM and Point Location

"""
# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
import arcpy
from sys import argv
import os


in_table_main = arcpy.GetParameterAsText(0)
clip_dem_ft = arcpy.GetParameterAsText(1)
output_folder = arcpy.GetParameterAsText(2)

Inundation_Field = arcpy.GetParameterAsText(3)

arcpy.env.scratchWorkspace = arcpy.GetParameterAsText(4)


arcpy.env.overwriteOutput = True

arcpy.MakeFeatureLayer_management(in_table_main,"working_lyr")



def Model1():
    with arcpy.da.SearchCursor("working_lyr",[Inundation_Field,"ModelNode","OBJECTID"]) as cursor:
        for item in cursor:
##            if item[2] != 999:
##                arcpy.AddMessage("Skipping where {0} = {1}".format("OBJECTID",item[2]))
##                continue

            arcpy.AddMessage("working on ModelNode {0} , where {1} = {2}".format(item[1],Inundation_Field,item[0]))

            whereClause = "{0} = {1}".format("OBJECTID",item[2])
            arcpy.AddMessage("Selecting Feature with  {0}".format(whereClause))
            arcpy.SelectLayerByAttribute_management("working_lyr", 'NEW_SELECTION',whereClause)


            in_table = arcpy.env.scratchWorkspace + os.path.sep +"Selection_{0}".format(item[1])

            arcpy.CopyFeatures_management("working_lyr", in_table)

            arcpy.AddMessage("Processing Buffer")
            New_Buffer = arcpy.env.scratchWorkspace + os.path.sep +   "New_Buffer_{0}".format(item[1])
            arcpy.Buffer_analysis(in_features=in_table, out_feature_class=New_Buffer, buffer_distance_or_field="1000 Feet", line_side="FULL", line_end_type="ROUND", dissolve_option="NONE", dissolve_field=[], method="PLANAR")
            arcpy.AddMessage(New_Buffer)
            

            arcpy.AddMessage("Process Contours")
            ContourVal = arcpy.env.scratchWorkspace + os.path.sep + "ContourVal_{0}".format(item[1])
            arcpy.AddMessage(ContourVal)
            arcpy.gp.Contour_sa(clip_dem_ft, ContourVal, 1000000, item[0], 1, "CONTOUR", None)

            Name_Contour_FeatureToPolygo = arcpy.env.scratchWorkspace + os.path.sep + "Name_Contour_FeatureToPolygo_{0}".format(item[1])
            arcpy.AddMessage("Feature to Polygon")
            arcpy.FeatureToPolygon_management([ContourVal], Name_Contour_FeatureToPolygo, "", "ATTRIBUTES", "")

            arcpy.AddMessage("Select Feature By Location")
            Name_Contour_FeatureToPolygo_2_, Output_Layer_Names, Count = arcpy.SelectLayerByLocation_management([Name_Contour_FeatureToPolygo], "INTERSECT", in_table, "", "NEW_SELECTION", "NOT_INVERT")

            arcpy.AddMessage("Writing output Feature Class")
            arcpy.FeatureClassToFeatureClass_conversion(Name_Contour_FeatureToPolygo_2_, output_folder, "{0}_Output".format(item[1]), "")

            arcpy.AddMessage("Deleting Temporary Files")

            arcpy.Delete_management(New_Buffer)
            arcpy.Delete_management(Name_Contour_FeatureToPolygo)
            arcpy.Delete_management(Name_Contour_FeatureToPolygo_2_)

            arcpy.AddMessage("-------------------------\n")






    
if __name__ == '__main__':
    # Global Environment settings
    Model1()
