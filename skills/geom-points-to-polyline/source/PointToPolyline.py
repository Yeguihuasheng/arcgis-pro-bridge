# -*- coding: UTF-8 -*-

import arcpy
import os

#ツール定義
class PointToPolyline(object):

  def __init__(self):
    self.label = "Point To Polyline"
    self.description = "Creates a Polyline feature class from specified point features."

    self.category = "TransformationShapes"
    self.canRunInBackground = False

  def getParameterInfo(self):

    param0 = arcpy.Parameter(
               displayName="Input Features",
               name="in_layer",
               datatype="GPFeatureLayer",
               parameterType="Required",
               direction="Input")

    param0.filter.list = ["Point"]#, "Multipoint"]

    param1 = arcpy.Parameter(
        displayName="GroupField",
        name="groupfield",
        datatype="Field",
        parameterType="Optional",
        direction="Input")

    param1.filter.list = ['Short', 'Long', 'Double', 'Single', 'Text']
    param1.parameterDependencies = [param0.name]

    param2 = arcpy.Parameter(
        displayName="SortField",
        name="sortfield",
        datatype="Field",
        parameterType="Optional",
        direction="Input")

    param2.filter.list = ['Short', 'Long', 'Double', 'Single', 'Text', 'OID']
    param2.parameterDependencies = [param0.name]

    param3 = arcpy.Parameter(
        displayName="Output Features",
        name="out_features",
        datatype="DEFeatureClass",
        parameterType="Required",
        #parameterType="Derived",
        direction="Output")

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
    groupField = parameters[1].valueAsText
    sortField = parameters[2].valueAsText
    outFeatures = parameters[3].valueAsText

    #messages.addMessage(inFeatures)
    #messages.addMessage(groupField)
    #messages.addMessage(sortField)
    #messages.addMessage(outFeatures)

    inDesc = arcpy.Describe(inFeatures)
    if (inDesc.dataType == "FeatureLayer"):
      inDesc = inDesc.featureClass
      
    inputHasM = "DISABLED"
    inputHasZ = "DISABLED"
    if (inDesc.hasM):
      inputHasM = "ENABLED"
    if (inDesc.hasZ):
      inputHasZ = "ENABLED "
    
    dirName, fcName = os.path.split(outFeatures)

    #create output
    arcpy.CreateFeatureclass_management(dirName, fcName, "POLYLINE", None, inputHasM, inputHasZ, inDesc.spatialReference)

    
    fields = arcpy.ListFields(inFeatures)
    oidField = ""
    gfield = None
    for field in fields:
      if (field.type == "OID"):
        oidField = field.name
      if (field.name == groupField):
        gfield = field

    if (not sortField):
      sortField = oidField

    #tempName = inFeatures

    if (groupField):
      arcpy.AddField_management(outFeatures, gfield.name, gfield.type, gfield.precision,
                          gfield.scale, gfield.length, gfield.aliasName, field_is_nullable="NULLABLE")    
    
    fieldList = []
    insertFieldList = []
    if (groupField):
      fieldList.append(groupField)
      insertFieldList.append(groupField)
      
    fieldList.append(sortField)
    fieldList.append("SHAPE@")
    insertFieldList.append("SHAPE@")

    with arcpy.da.InsertCursor(outFeatures, insertFieldList) as inCursor:
      with arcpy.da.SearchCursor(inFeatures, fieldList) as cursor:
        pntList = []
        isFirstTime = True
        preGroup = None
        
        for row in sorted(cursor):

          if (isFirstTime):
            isFirstTime = False
            preGroup = row[0]
          elif (groupField and preGroup != row[0]):
            if (isinstance(row[-1] , arcpy.PointGeometry)):
              insertRow = (preGroup,) + (arcpy.Polyline(arcpy.Array(pntList)),)
              inCursor.insertRow(insertRow)
            preGroup = row[0]
            pntList = []

          if (isinstance(row[-1] , arcpy.PointGeometry)):
            pntList.append(row[-1].centroid)

          #if (groupField):
          #  messages.addMessage(row[0])
          #messages.addMessage(row[-2])

        if (not groupField):
          insertRow = (arcpy.Polyline(arcpy.Array(pntList)),)
          inCursor.insertRow(insertRow)
        else:
          insertRow = (preGroup,) + (arcpy.Polyline(arcpy.Array(pntList)),)
          inCursor.insertRow(insertRow)

            
