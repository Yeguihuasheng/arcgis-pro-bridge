# import modules
import arcpy
from os import path

inputMetadata = arcpy.GetParameterAsText(0)
outputFolder = arcpy.GetParameterAsText(1)
datasets = inputMetadata.split(";")


def xmlExport(fc):
    """
    export metadata from feature class and save as xml file
    """
    # arcgis install directory
    dir = arcpy.GetInstallInfo("desktop")["InstallDir"]
    # exact copy xslt transformation
    xslt = dir + "Metadata/Stylesheets/gpTools/exact copy of.xslt"
    # set output directory
    out_dir = outputFolder
    # set arcpy workspace
    arcpy.env.workspace = out_dir
    # set workspace overwrite true
    arcpy.env.overwriteOutput = True
    #assemble output xml file name
    output_xml = path.join(out_dir, path.basename(fc) + ".xml")
    #XSLT transforamtion
    arcpy.XSLTransform_conversion(fc, xslt, output_xml)


counter = 1
# loop datasets
for inputFC in datasets:
    inputFC = inputFC.replace("'", "")
    # set arcpy Describe object from input
    inputdesc = arcpy.Describe(inputFC)
    arcpy.AddMessage("\n## {} of {} : {}".format(counter, len(datasets), inputdesc.baseName))
    # check input data element is in the list
    if inputdesc.dataType in ["FeatureClass", "RasterDataset", "Workspace", "ShapeFile", "FeatureDataset", "Table", "TextFile"]:
        xmlfile = xmlExport(inputFC)
    else:
        arcpy.AddMessage("Input data type not supported.")
        quit()

    counter += 1

arcpy.AddMessage(" ")