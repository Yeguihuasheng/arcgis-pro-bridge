# -*- coding: UTF-8 -*-
import arcpy
import os

#ツール定義
class AddPointCountField(object):
  def __init__(self):
    self.label = "Add Point Count Field"
    self.description = "Adds a Point Count field to a feature layer."

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
        fields = arcpy.ListFields(inFeatures)
        for field in fields:
          if (field.name.upper() == "PointCount" or field.name.upper() == "PartCount"):
            parameters[0].setWarningMessage("The value of the [PointCount/PartCount] field will be overwritten.")
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
    if (not "PointCount" in fieldList):
      arcpy.AddField_management(inFeatures, "PointCount", "LONG", 9)
    if (not "PartCount" in fieldList):
      arcpy.AddField_management(inFeatures, "PartCount", "LONG", 9)
    
    calcPartCount = "!" + shpFieldName + "!.partCount"
    calcPointCount = "!" + shpFieldName + "!.pointCount"
    
    # 2 loop... update cursor?
    arcpy.CalculateField_management(inFeatures, "PointCount", calcPointCount, "PYTHON_9.3")
    arcpy.CalculateField_management(inFeatures, "PartCount", calcPartCount, "PYTHON_9.3")
    
    
