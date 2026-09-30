# -*- coding: UTF-8 -*-

import arcpy
import os

#ツール定義
class AddLengthField(object):
  def __init__(self):
    self.label = "Add Length Field"
    self.description = "Adds a Length field to a Polyline/Polygon feature layer."

    self.category = "Fields"
    self.canRunInBackground = False

  def getParameterInfo(self):
    param0 = arcpy.Parameter(
               displayName="Input Features",
               name="in_features",
               datatype="GPFeatureLayer",
               parameterType="Required",
               direction="Input")
    param0.filter.list = ["Polygon", "Polyline"]

    param1 = arcpy.Parameter(
        displayName="Output Features",
        name="out_features",
        datatype="GPFeatureLayer",
        parameterType="Derived",
        direction="Output")
    
    param2 = arcpy.Parameter(
        displayName="Length Calc Type",
        name="cal_type",
        datatype="GPString",
        parameterType="Required",
        direction="Input")

    param2.filter.type = "ValueList"
    param2.filter.list = ["GEODESIC",
                          "GREAT_ELLIPTIC",
                          "LOXODROME",
                          "PLANAR",
                          "PRESERVE_SHAPE"]
    
    param3 = arcpy.Parameter(
        displayName="Length Unit",
        name="length_unit",
        datatype="GPString",
        parameterType="Required",
        direction="Input")

    param3.filter.type = "ValueList"
    param3.filter.list = ["CENTIMETERS",
                          "DECIMETERS",
                          "FEET",
                          "INCHES",
                          "KILOMETERS",
                          "METERS",
                          "MILES",
                          "MILLIMETERS",
                          "NAUTICALMILES",
                          "YARDS"
                          ]
    
    params = [param0, param1, param2, param3]
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
          if (field.name.upper() == "LENGTH"):
            parameters[0].setWarningMessage("The value of the [Length] field will be overwritten.")
            break
    return
  
  def execute(self, parameters, messages):
    
    inFeatures = parameters[0].valueAsText
    calcType = parameters[2].valueAsText
    unit = parameters[3].valueAsText
    
    fields = arcpy.ListFields(inFeatures)
    fieldList = []
    shpFieldName = ""
    
    for field in fields:
      if (field.type == "Geometry"):
        shpFieldName = field.name
      
      fieldList.append(field.name)
    #fieldList.append("SHAPE@")
    if (not "LENGTH" in fieldList):
      arcpy.AddField_management(inFeatures, "LENGTH", "DOUBLE", 18, 11)
    
    #calcArea = "!" + shpFieldName + '!.getArea(' + calcType + "," + unit + ")"
    calcArea = '!{shpFieldName}!.getLength("{calcType}" , "{unit}")'.format(shpFieldName=shpFieldName, calcType=calcType, unit=unit)
    
    arcpy.CalculateField_management(inFeatures, "LENGTH", calcArea, "PYTHON_9.3")
    
