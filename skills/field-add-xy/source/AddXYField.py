# -*- coding: UTF-8 -*-
import arcpy
import os

#ツール定義
class AddXYField(object):
  def __init__(self):
    self.label = "Add XY Field"
    self.description = "Adds a XY field to a feature layer."

    self.category = "Fields"
    self.canRunInBackground = False

  def getParameterInfo(self):
    param0 = arcpy.Parameter(
               displayName="Input Features",
               name="in_features",
               datatype="GPFeatureLayer",
               parameterType="Required",
               direction="Input")
    param0.filter.list = ["Point","Multipoint","Polyline","Polygon"]

    param1 = arcpy.Parameter(
               displayName="Point Location",
               name="point_location",
               datatype="GPString",
               parameterType="Required",
               direction="Input")
    
    param1.filter.type = "ValueList"
    param1.filter.list = ["POINT"]
    param1.enabled = False
    param1.value = "POINT"

    param2 = arcpy.Parameter(
        displayName="Output Features",
        name="out_features",
        datatype="GPFeatureLayer",
        parameterType="Derived",
        direction="Output")

    params = [param0, param1, param2]
    return params

  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    if parameters[0]:
      inFeatures = parameters[0].valueAsText
      if (inFeatures):
        inDesc = arcpy.Describe(inFeatures)
        if (inDesc.dataType == "FeatureLayer"):
          inDesc = inDesc.featureClass

        ptLocation = parameters[1]

        if ( (inDesc.shapeType == "Polygon" or
            inDesc.shapeType == "Multipoint") and not "CENTROID" in ptLocation.filter.list):
          ptLocation.filter.list = ["CENTROID", "LABELPOINT", "TRUECENTROID"]
          ptLocation.enabled = True
          ptLocation.value = "centroid"
        
        elif (inDesc.shapeType == "Polyline" and not "START" in ptLocation.filter.list):
          ptLocation.filter.list = ["START", "MID", "END"]
          ptLocation.enabled = True
          ptLocation.value = "START"
        
        elif (inDesc.shapeType == "Point" and not "POINT" in ptLocation.filter.list):
          ptLocation.filter.list = ["POINT"]
          ptLocation.enabled = False
          ptLocation.value = "POINT"
        
        parameters[1] = ptLocation
    
    return
  
  def updateMessages(self, parameters):
    inFeatures = parameters[0].valueAsText
    if (inFeatures):
      inDesc = arcpy.Describe(inFeatures)
      if (inDesc.dataType == "FeatureLayer"):
        inDesc = inDesc.featureClass
      # message clear ( check fieldname )
      parameters[0].clearMessage()
      fields = arcpy.ListFields(inFeatures)
      for field in fields:
        if (field.name.upper() == "X" or field.name.upper() == "Y"):
          parameters[0].setWarningMessage("The value of the [X/Y] field will be overwritten.")
          break

    
    return
  
  def execute(self, parameters, messages):
    
    inFeatures = parameters[0].valueAsText
    pointType = parameters[1].valueAsText

    fields = arcpy.ListFields(inFeatures)
    fieldList = []
    shpFieldName = ""
    
    for field in fields:
      if (field.type == "Geometry"):
        shpFieldName = field.name
      
      fieldList.append(field.name)
    #fieldList.append("SHAPE@")
    if (not "X" in fieldList):
      arcpy.AddField_management(inFeatures, "X", "DOUBLE", 18, 11)
    if (not "Y" in fieldList):
      arcpy.AddField_management(inFeatures, "Y", "DOUBLE", 18, 11)

    calcX = "!" + shpFieldName + "!.centroid.X"
    calcY = "!" + shpFieldName + "!.centroid.Y"
    if (pointType == "TRUECENTROID"):
      calcX = "!" + shpFieldName + "!.trueCentroid.X"
      calcY = "!" + shpFieldName + "!.trueCentroid.Y"
    elif (pointType == "LABELPOINT"):
      calcX = "!" + shpFieldName + "!.labelPoint.X"
      calcY = "!" + shpFieldName + "!.labelPoint.Y"
    elif (pointType == "START"):
      calcX = "!" + shpFieldName + "!.firstPoint.X"
      calcY = "!" + shpFieldName + "!.firstPoint.Y"
    elif (pointType == "MID"):
      calcX = "!" + shpFieldName + "!.positionAlongLine(0.5,True).firstPoint.X"
      calcY = "!" + shpFieldName + "!.positionAlongLine(0.5,True).firstPoint.Y"
    elif (pointType == "END"):
      calcX = "!" + shpFieldName + "!.lastPoint.X"
      calcY = "!" + shpFieldName + "!.lastPoint.Y"

    # 2 loop... update cursor?
    arcpy.CalculateField_management(inFeatures, "X", calcX, "PYTHON_9.3")
    arcpy.CalculateField_management(inFeatures, "Y", calcY, "PYTHON_9.3")

    
