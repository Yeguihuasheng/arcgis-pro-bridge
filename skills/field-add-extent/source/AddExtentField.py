# -*- coding: UTF-8 -*-
import arcpy
import os

#ツール定義
class AddExtentField(object):
  def __init__(self):
    self.label = "Add Extent Field"
    self.description = "Adds a Extent field to a feature layer."

    self.category = "Fields"
    self.canRunInBackground = False

  def getParameterInfo(self):
    param0 = arcpy.Parameter(
               displayName="Input Features",
               name="in_features",
               datatype="GPFeatureLayer",
               parameterType="Required",
               direction="Input")
    param0.filter.list = ["Multipoint","Polyline","Polygon"]

    param1 = arcpy.Parameter(
        displayName="Output Features",
        name="out_features",
        datatype="GPFeatureLayer",
        parameterType="Derived",
        direction="Output")

    params = [param0, param1]
    return params

  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    
    return
  
  def updateMessages(self, parameters):

    if parameters[0]:
      inFeatures = parameters[0].valueAsText
      if (inFeatures):
        inDesc = arcpy.Describe(inFeatures)
        if (inDesc.dataType == "FeatureLayer"):
          inDesc = inDesc.featureClass
        # message clear ( check fieldname )
        # parameters[0].clearMessage()
        fields = arcpy.ListFields(inFeatures)
        for field in fields:
          if (field.name.upper() == "MINX" or field.name.upper() == "MINY" or
              field.name.upper() == "MAXX" or field.name.upper() == "MAXY"):
            parameters[0].setWarningMessage("The value of the [Min/Max X/Y] field will be overwritten.")
            break
    return
  
  def execute(self, parameters, messages):
    
    inFeatures = parameters[0].valueAsText
    
    fields = arcpy.ListFields(inFeatures)
    fieldList = []
    shpFieldName = ""
    
    for field in fields:
      if (field.type == "Geometry"):
        shpFieldName = field.name
      
      fieldList.append(field.name)
    #fieldList.append("SHAPE@")
    if (not "MINX" in fieldList):
      arcpy.AddField_management(inFeatures, "MINX", "DOUBLE", 18, 11)
    if (not "MINY" in fieldList):
      arcpy.AddField_management(inFeatures, "MINY", "DOUBLE", 18, 11)
    if (not "MAXX" in fieldList):
      arcpy.AddField_management(inFeatures, "MAXX", "DOUBLE", 18, 11)
    if (not "MAXY" in fieldList):
      arcpy.AddField_management(inFeatures, "MAXY", "DOUBLE", 18, 11)

    calcMinX = "!" + shpFieldName + "!.extent.XMin"
    calcMinY = "!" + shpFieldName + "!.extent.YMin"
    calcMaxX = "!" + shpFieldName + "!.extent.XMax"
    calcMaxY = "!" + shpFieldName + "!.extent.YMax"
    # 4 loop... update cursor?
    arcpy.CalculateField_management(inFeatures, "MINX", calcMinX, "PYTHON_9.3")
    arcpy.CalculateField_management(inFeatures, "MINY", calcMinY, "PYTHON_9.3")
    arcpy.CalculateField_management(inFeatures, "MAXX", calcMaxX, "PYTHON_9.3")
    arcpy.CalculateField_management(inFeatures, "MAXY", calcMaxY, "PYTHON_9.3")
    
