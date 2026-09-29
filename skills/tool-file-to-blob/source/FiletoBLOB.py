"""
FiletoBLOB.py
Performs a table join to associate image filenames with feature IDs, then reads 
the corresponding files from a local directory and inserts them directly into 
a BLOB field within the feature class. Cleans up the joined fields upon completion.

Dependencies: arcpy
"""
import arcpy
def script_tool(outFeatureClass, inFolder, inFieldName, outFieldName):
    inFields = []
    inFields.append(inFieldName)
    inFields.append(outFieldName)
    #print(inFields)
    features = arcpy.da.UpdateCursor(outFeatureClass,inFields)
    for feature in features:
        #print(feature[0])
        inRaster = str(inFolder) + "\\" + feature[0]
        #print(inRaster)
        with open(inRaster, "rb") as f:
            #print(f.read())
            feature[1] = f.read()
            features.updateRow(feature)
    return
if __name__ == "__main__":
    # Set the feature class has BLOB field
    outFeatureClass = arcpy.GetParameterAsText(0)
    # Set the ID field in outFeatureClass
    in_field = arcpy.GetParameterAsText(1)
    # Set the join table has ID-filename relationship
    join_table = arcpy.GetParameterAsText(2)
    # Set the ID field in join table
    join_field = arcpy.GetParameterAsText(3)
    # Set the name of the field that has image filename.
    inFieldName = arcpy.GetParameterAsText(4)
    # Set the photo directory
    inFolder = arcpy.GetParameterAsText(5)
    # Set the field name that will store the image BLOB.
    outFieldName = arcpy.GetParameterAsText(6)
    
    arcpy.management.JoinField(outFeatureClass,in_field,join_table,join_field,inFieldName)
    script_tool(outFeatureClass, inFolder, inFieldName, outFieldName)
    arcpy.DeleteField_management(outFeatureClass, inFieldName, "DELETE_FIELDS")
    #arcpy.SetParameterAsText(4, "Result")

