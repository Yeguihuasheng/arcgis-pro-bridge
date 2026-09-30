# -*- coding: UTF-8 -*-

import arcpy
import os

import numpy as np

#ツール定義
class RandomPoints(object):
    
  def __init__(self):
    self.label = "Random Points"
    self.description = "Creates a specified number of random point features. Random points can be generated in a inside polygon features."

    self.category = "TransformationShapes"
    self.canRunInBackground = False

  def getParameterInfo(self):

    param0 = arcpy.Parameter(
        displayName="Input Features",
        name="in_layer",
        datatype="GPFeatureLayer",
        parameterType="Required",
        direction="Input")
    param0.filter.list = ["Polygon"]

    param1 = arcpy.Parameter(
        displayName="Point Count Field",
        name="in_rndPointNumCol",
        datatype="Field",
        parameterType="Optional",
        direction="Input")

    param1.filter.list = ['Short', 'Long']
    param1.parameterDependencies = [param0.name]

        
    param2 = arcpy.Parameter(
        displayName="Point Count [If not field]",
        name="in_rndPointNum",
        datatype="GPLong",
        parameterType="Required",
        direction="Input")
    param2.value = 100

    param3 = arcpy.Parameter(
        displayName="Output Features",
        name="out_features",
        datatype="DEFeatureClass",
        parameterType="Required",
        direction="Output")

    return [param0, param1, param2, param3]

  def isLicensed(self):
    return True

  def updateParameters(self, parameters):
    return

  def updateMessages(self, parameters):
    return

  def execute(self, parameters, messages):
    try:
      layer = parameters[0].value
      cntCol = parameters[1].valueAsText
      pntNum = parameters[2].value
      outFullName = parameters[3].valueAsText

      #messages.addMessage(layer.name)
      #if not (cntCol is None):
      #  messages.addMessage(cntCol)
      #messages.addMessage(outFullName)

      geomType = "POINT"
      template = None
      outWs = os.path.dirname(outFullName)
      outFc = os.path.basename(outFullName)

      # messages.addMessage("WS:{0} / Name:{1}".format(outWs,outFc))
      has_m = "DISABLED"
      has_z = "DISABLED"
      spRef = None

      dataset = layer.dataSource
      spRef = arcpy.Describe(dataset).spatialReference

      arcpy.CreateFeatureclass_management(outWs, outFc, geomType, template, has_m, has_z, spRef)
      arcpy.AddField_management(outFullName, "orgOid", "LONG", 10, "", "", "OriginalOID", "NON_NULLABLE")

      oidCol = arcpy.Describe(layer).OIDFieldName
      outcols = [oidCol,"SHAPE@"]
      if not (cntCol is None):
        outcols.append(cntCol)

      # for Progress step count
      result = arcpy.GetCount_management(layer)
      count = int(result.getOutput(0))
      arcpy.SetProgressor("step", "Inserting ...", 0, count, 1)

      with arcpy.da.SearchCursor(layer, outcols) as cursor, arcpy.da.InsertCursor(outFullName, ["orgOid","SHAPE@"]) as ins:
        for row in cursor:
          x = 0
          loopCnt = pntNum
          if not (cntCol is None) and not (row[2] is None):
            loopCnt = row[2]

          while x < loopCnt:
            px = row[1].extent.XMin + row[1].extent.width * np.random.random()
            py = row[1].extent.YMin + row[1].extent.height * np.random.random()
            pt = arcpy.Point(px,py)
                        
            #caution: loop end is contains == true
            if row[1].contains(pt):
              x += 1
              ins.insertRow([ row[0], pt ])
          # step count
          arcpy.SetProgressorPosition()
                        
    except Exception as e:
      messages.AddErrorMessage(e.message)
