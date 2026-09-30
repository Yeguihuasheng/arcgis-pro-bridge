import zipper
import arcpy

try:
    # Inputs
    shapefile = arcpy.GetParameterAsText(0)
    zipfile = arcpy.GetParameterAsText(1)
    mode = arcpy.GetParameterAsText(2)

    shape_zipper = zipper.ShapefileZipper()  # Create Class Instance
    result = shape_zipper.zip_shapefile(input_shapefile=shapefile, output_zipfile=zipfile,
                                        zip_file_mode=mode)

    if result:
        arcpy.SetParameterAsText(3, result)
        arcpy.AddMessage("!!!!!!!!!!!!!\n@@ SUCCESS @@\n!!!!!!!!!!!!!\nResult:  " + result)
    else:
        arcpy.AddMessage("FILE NOT CREATED")
except:
    arcpy.AddError("Opps...something done broke.")