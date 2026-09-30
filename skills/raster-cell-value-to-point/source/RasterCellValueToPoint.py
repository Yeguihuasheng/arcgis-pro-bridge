# -*- coding: UTF-8 -*-

import arcpy

#ツール定義
class RasterCellValueToPoint(object):
  def __init__(self):
    self.label = "Raster Cell Value to Point Attribute"
    self.description = "Set Point Attributes from Raster Pixcel value."

    self.category = "Fields"
    self.canRunInBackground = False

  def getParameterInfo(self):
    param0 = arcpy.Parameter(
    displayName="Input Raster",
    name="in_raster",
    datatype="GPRasterLayer",
    parameterType="Required",
    direction="Input")

    param1 = arcpy.Parameter(
      displayName="Input Features",
      name="in_features",
      datatype="GPFeatureLayer",
      parameterType="Required",
      direction="Input")

    param2 = arcpy.Parameter(
      displayName="Output Features",
      name="out_features",
      datatype="GPFeatureLayer",
      parameterType="Derived",
      direction="Output")
        
    param2.parameterDependencies = [param1.name]
    param2.schema.clone = True
        
    return [param0, param1, param2]

  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    return

  def updateMessages(self, parameters):
    raster = parameters[0].valueAsText
    feature = parameters[1].valueAsText
      
    if (feature and raster):
      inDesc = arcpy.Describe(feature)
      if (inDesc.dataType == "FeatureLayer"):
        inDesc = inDesc.featureClass
        
      parameters[0].clearMessage()

      desc = arcpy.Describe(raster)
      for bandIndex in range(desc.bandCount):
        fname = 'BAND' + str(bandIndex)
          
        fields = arcpy.ListFields(feature)
        for field in fields:
          if (field.name.upper() == fname):
            parameters[1].setWarningMessage("The value of the [band n] field will be overwritten.")
            break
        
    return

  def execute(self, parameters, messages):
    raster = parameters[0].valueAsText
    feature = parameters[1].valueAsText

    fields = arcpy.ListFields(feature)
    fieldList = [field.name for field in fields]

    addFields = []
    desc = arcpy.Describe(raster)
    for bandIndex in range(desc.bandCount):
      fname = 'BAND' + str(bandIndex)
      addFields.append(fname)
      if (not fname in fieldList):
        arcpy.AddField_management(feature, fname, "DOUBLE", 18, 11)

      addFields.append('SHAPE@XY')
      bandIndex=';'.join( str(x) for x in range(1,desc.bandCount + 1))
        
    with arcpy.da.UpdateCursor(feature, addFields) as cursor:
      for row in cursor:
                
        fname = 'BAND' + str(bandIndex)
        result = arcpy.GetCellValue_management(raster, str((row[-1])[0]) + " " + str((row[-1])[1]), bandIndex)

        res = result.getOutput(0).split('\\n')

        for inx in range(len(res)):  
          cellValue = float(res[inx])
          row[inx] = cellValue
        #Update the FC row
        cursor.updateRow(row)
    return
