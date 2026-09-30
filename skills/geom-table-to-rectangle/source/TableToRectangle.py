# -*- coding: UTF-8 -*-

import arcpy

import os
import codecs
import datetime
#import pytz

#ツール定義
class TableToRectangle(object):

  def __init__(self):
    self.label = "Table To Rectangle"
    self.description = "Creates a rectangular polygon from four corner coordinates."

    self.category = "DataManagement"
    self.canRunInBackground = False

  def getParameterInfo(self):

    param0 = arcpy.Parameter(
               displayName="In Records",
               name="in_layer",
               datatype=["GPTableView", "DETable"],
               parameterType="Required",
               direction="Input")

    param1 = arcpy.Parameter(
               displayName="SpatialReference",
               name="spref",
               datatype="GPSpatialReference",
               parameterType="Required",
               direction="Input")

    param2 = arcpy.Parameter(
        displayName="MinX",
        name="MinX",
        datatype="Field",
        parameterType="Required",
        direction="Input")
    param2.filter.list = ['Short', 'Long', 'Double', 'Single']
    param2.parameterDependencies = [param0.name]

    param3 = arcpy.Parameter(
        displayName="MinY",
        name="MinY",
        datatype="Field",
        parameterType="Required",
        direction="Input")
    param3.filter.list = ['Short', 'Long', 'Double', 'Single']
    param3.parameterDependencies = [param0.name]

    param4 = arcpy.Parameter(
        displayName="MaxX",
        name="MaxX",
        datatype="Field",
        parameterType="Required",
        direction="Input")
    param4.filter.list = ['Short', 'Long', 'Double', 'Single']
    param4.parameterDependencies = [param0.name]

    param5 = arcpy.Parameter(
        displayName="MaxY",
        name="MaxY",
        datatype="Field",
        parameterType="Required",
        direction="Input")
    param5.filter.list = ['Short', 'Long', 'Double', 'Single']
    param5.parameterDependencies = [param0.name]

    param6 = arcpy.Parameter(
        displayName="Output Features",
        name="out_features",
        datatype="DEFeatureClass",
        parameterType="Required",
        #parameterType="Derived",
        direction="Output")

    params = [param0, param1, param2, param3, param4, param5, param6]
    return params

  
  def isLicensed(self):        
    return True

  def updateParameters(self, parameters):
    return
  
  def updateMessages(self, parameters):
    return
  
  def execute(self, parameters, messages):

    records = parameters[0].valueAsText
    spRef = parameters[1].value
    minXField = parameters[2].valueAsText
    minYField = parameters[3].valueAsText
    maxXField = parameters[4].valueAsText
    maxYField = parameters[5].valueAsText

    outFeatures = parameters[6].valueAsText
    dirName, fcName = os.path.split(outFeatures)

    arcpy.CreateFeatureclass_management(dirName, fcName, "POLYGON", None, "DISABLED", "DISABLED", spRef)
    arcpy.AddField_management(outFeatures, "LINK_ID", "LONG")

    with arcpy.da.SearchCursor(records, [minXField, minYField, maxXField, maxYField, 'OID@']) as cursor:
      with arcpy.da.InsertCursor(outFeatures, ["LINK_ID", "SHAPE@"]) as inCursor:
        for row in cursor:
          rect = arcpy.Extent(row[0],row[1],row[2],row[3])
          
          insertRow = (row[4], arcpy.Polygon(arcpy.Array([rect.lowerLeft, rect.upperLeft, rect.upperRight, rect.lowerRight, rect.lowerLeft])))
          inCursor.insertRow(insertRow)
      
