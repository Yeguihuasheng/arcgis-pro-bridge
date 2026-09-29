"""
BLOBtoFile.py
Extracts Binary Large Object (BLOB) data (such as inspection photos) from a 
geodatabase feature class. Iterates through the records and exports the binary 
data to a specified local directory as individual files.

Dependencies: arcpy, os
"""
import arcpy
import os
def script_tool(fc,fieldsName,fileType,destFolder):
    """Script code goes below"""
    # For each row, print the WELL_ID and WELL_TYPE fields, and
    # the feature's x,y coordinates
    with arcpy.da.SearchCursor(fc, fieldsName) as cursor:
        for row in cursor:
            fileName = str(row[0])+fileType
            file_binary = row[1]
            open(destFolder + os.sep + fileName, 'wb').write(file_binary.tobytes())
            del row
            del file_binary
            del fileName
    return
if __name__ == "__main__":
    # Set the input featureclass with BLOB
    fc = arcpy.GetParameterAsText(0)
    # Set the field being used to name photos
    fileName_field = arcpy.GetParameterAsText(1)
    # Set the field has BLOB
    BLOB_field = arcpy.GetParameterAsText(2)
    # Set the file extension
    fileType = arcpy.GetParameterAsText(3)
    # Set the folder to save extracted photos
    destFolder = arcpy.GetParameterAsText(4)
    # Example input values for testing:
    # fc = r"C:\GIS_Data\Sample.gdb\Sign_Support"
    # fieldsName = ["SUPPORT_ID", "SIGN_SUPPORT_PHOTO"]
    fieldsName = []
    fieldsName.append(fileName_field)
    fieldsName.append(BLOB_field)
    fileType = '.' + fileType
    script_tool(fc,fieldsName,fileType,destFolder)
    #arcpy.SetParameterAsText(2, "Result")


