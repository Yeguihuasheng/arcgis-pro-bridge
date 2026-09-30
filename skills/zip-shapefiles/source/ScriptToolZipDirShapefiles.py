import zipper
import arcpy

try:
    # Inputs
    dir = arcpy.GetParameterAsText(0)
    zipfile = arcpy.GetParameterAsText(1)
    mode = arcpy.GetParameterAsText(2)

    shape_zipper = zipper.ShapefileZipper()  # Create Class Instance
    result = shape_zipper.zip_shapefile_directory(input_dir=dir, output_zipfile=zipfile, zip_file_mode=mode)

    if len(result) > 0:
        results = str(result)
        arcpy.SetParameterAsText(3, results)
        arcpy.AddMessage("!!!!!!!!!!!!!\n@@ SUCCESS @@\n!!!!!!!!!!!!!\nResult:  " + results)
    else:
        raise
except:
    arcpy.AddError("ZIP FILES NOT CREATED!")