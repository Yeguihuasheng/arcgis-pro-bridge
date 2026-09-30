# -*- coding: UTF-8 -*-

import arcpy

import os
import codecs
import datetime
#import pytz

#ツール定義
class TableToCircle(object):

  def __init__(self):
    self.label = "Table To Circle"
    self.description = "Creates a circular  polygon from a table."

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
        displayName="CenterX",
        name="CenterX",
        datatype="Field",
        parameterType="Required",
        direction="Input")
    param2.filter.list = ['Short', 'Long', 'Double', 'Single']
    param2.parameterDependencies = [param0.name]

    param3 = arcpy.Parameter(
        displayName="CenterY",
        name="CenterY",
        datatype="Field",
        parameterType="Required",
        direction="Input")
    param3.filter.list = ['Short', 'Long', 'Double', 'Single']
    param3.parameterDependencies = [param0.name]

    param4 = arcpy.Parameter(
        displayName="radius",
        name="radius",
        datatype="Field",
        parameterType="Required",
        direction="Input")
    param4.filter.list = ['Short', 'Long', 'Double', 'Single']
    param4.parameterDependencies = [param0.name]

    param5 = arcpy.Parameter(
        displayName="Output Features",
        name="out_features",
        datatype="DEFeatureClass",
        parameterType="Required",
        #parameterType="Derived",
        direction="Output")

    params = [param0, param1, param2, param3, param4, param5]
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
    cxField = parameters[2].valueAsText
    cyField = parameters[3].valueAsText
    rField = parameters[4].valueAsText
    
    outFeatures = parameters[5].valueAsText
    dirName, fcName = os.path.split(outFeatures)

    arcpy.CreateFeatureclass_management(dirName, fcName, "POLYGON", None, "DISABLED", "DISABLED", spRef)
    arcpy.AddField_management(outFeatures, "LINK_ID", "LONG")

    with arcpy.da.SearchCursor(records, [cxField, cyField, rField, 'OID@']) as cursor:
      with arcpy.da.InsertCursor(outFeatures, ["LINK_ID", "SHAPE@"]) as inCursor:
        for row in cursor:
          pnt = arcpy.Point(row[0], row[1])
          pnt_geometry = arcpy.PointGeometry(pnt, spRef)

          buffered = None
          if (row[2] != 0):
            buffered = pnt_geometry.buffer(row[2])

          insertRow = (row[3], buffered)
          inCursor.insertRow(insertRow)
      
