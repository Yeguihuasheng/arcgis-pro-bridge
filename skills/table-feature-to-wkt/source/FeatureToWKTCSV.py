# -*- coding: UTF-8 -*-

import arcpy

import re
import os
import codecs

#ツール定義
class FeatureToWKTCSV(object):

  def __init__(self):
    self.label = "Feature To UTF-8 WKT CSV"
    self.description = "Creates a UTF-8 WKT CSV from specified features."

    self.category = "DataManagement"
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
        displayName="Output CSV",
        name="out_csv",
        datatype="DEFile",
        parameterType="Required",
        #parameterType="Derived",
        direction="Output")
    param1.filter.list = ['csv', 'txt']

    params = [param0, param1]
    return params

  
  def isLicensed(self):        
    return True

  def updateParameters(self, parameters):
    return
  
  def updateMessages(self, parameters):
    return
  
  def execute(self, parameters, messages):
    inFeatures = parameters[0].valueAsText
    outCsv = parameters[1].valueAsText

    inDesc = arcpy.Describe(inFeatures)
    if (inDesc.dataType == "FeatureLayer"):
      inDesc = inDesc.featureClass
      
    fields = arcpy.ListFields(inFeatures)
    shpField = ""
    fieldList = []
    typeList = []
    
    for field in fields:
      if (field.type == "Geometry"):
        shpField = field.name
      else:
        fieldList.append(field.name)
        typeList.append(field.type)
    
    fieldList.append("SHAPE@WKT")

    with arcpy.da.SearchCursor(inFeatures, fieldList) as cursor:
      with codecs.open(outCsv, 'w', 'utf-8') as csvFile:
        #header
        for field in fieldList:
          if field != "SHAPE@WKT":
            csvFile.write( field )
            csvFile.write( "," )
          else:
            csvFile.write( "WKT" )
        csvFile.write( '\r\n' )
        
        isFirstTime = True
        for row in cursor:
          if (isFirstTime):
            isFirstTime = False
          else:
            csvFile.write( '\r\n' )

          index = 0
          for ftype in typeList:
            val = row[index]
            if ftype != 'SmallInteger' \
               and ftype != 'Integer' \
               and ftype != 'Single' \
               and ftype != 'Double' \
               and ftype != 'OID':
              csvFile.write( '"' )
              if val in '"':
                val = val.replace('"', '""')
              csvFile.write( val )
              csvFile.write( '"' )
            else:
              csvFile.write( str(val) )
                
            csvFile.write( ',' )
            
            index=index+1
            #end loop field
          if row[-1]:
            csvFile.write( '"' )
            csvFile.write( re.sub( '\r\n|\n|\r', '', row[-1] ) )
            csvFile.write( '"' )
          else:
            messages.addWarningMessage( str(row[0]) + " None Geometry")
            
    
 
