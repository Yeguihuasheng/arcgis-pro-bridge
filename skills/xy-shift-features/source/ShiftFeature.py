# -*- coding: UTF-8 -*-

import arcpy
import os

#ツール定義
class ShiftFeature(object):

  def __init__(self):
    self.label = "Shift Feature"
    self.description = "Creates a shift feature class from specified xy shift."

    self.category = "TransformationShapes"
    self.canRunInBackground = False

  def getParameterInfo(self):
    param0 = arcpy.Parameter(
               displayName="Input Features",
               name="in_layer",
               datatype="GPFeatureLayer",
               parameterType="Required",
               direction="Input")

    param0.filter.list = ["Point", "Multipoint", "Polyline", "Polygon"]

    param1 = arcpy.Parameter(
        displayName="Output Features",
        name="out_features",
        datatype="DEFeatureClass",
        parameterType="Required",
        #parameterType="Derived",
        direction="Output")


    param2 = arcpy.Parameter(
        displayName="x shift",
        name="x_shift",
        datatype="GPDouble",
        parameterType="Required",
        direction="Input")

    param3 = arcpy.Parameter(
        displayName="y shift",
        name="y_shift",
        datatype="GPDouble",
        parameterType="Required",
        direction="Input")

    params = [param0, param1, param2, param3]
    return params

  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    return
  
  def updateMessages(self, parameters):
    return
  
  def execute(self, parameters, messages):
    
    inFeatures = parameters[0].valueAsText
    outFeatures = parameters[1].valueAsText
    x_shift = parameters[2].value
    y_shift = parameters[3].value

    #create output
    arcpy.CopyFeatures_management(inFeatures, outFeatures)

    result = arcpy.GetCount_management(inFeatures)
    count = int(result.getOutput(0))
    arcpy.SetProgressor("step", "Shifting ...", 0, count, 1)

    with arcpy.da.UpdateCursor(inFeatures, ['SHAPE@XY']) as cursor:
      for row in cursor:
        cursor.updateRow([[row[0][0] + (x_shift or 0),
                           row[0][1] + (y_shift or 0)]])
        
        arcpy.SetProgressorPosition()
