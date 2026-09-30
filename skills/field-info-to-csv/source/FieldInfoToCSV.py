# -*- coding: UTF-8 -*-

import arcpy

import sys
import codecs
import os

#ツール定義
class FieldInfoToCSV(object):

  def __init__(self):
    self.label = "FieldInfo to CSV"
    self.description = "Creates a Fields information CSV from specified features."

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

    enc = sys.stdin.encoding
    messages.addMessage(enc)

    with codecs.open(outCsv, 'w', enc) as csvFile:
      csvFile.write( 'NAME,ALIAS,DEFAULT,DOMAIN,EDITABLE,NULLABLE,LENGTH,PRECISION,REQUIRED,SCLAE,TYPE' )
      csvFile.write( os.linesep )
      for field in fields:
        csvFile.write(field.name)
        csvFile.write( "," )
        csvFile.write(field.aliasName)
        csvFile.write( "," )
        if field.defaultValue:
          csvFile.write(field.defaultValue)
        csvFile.write( "," )
        if field.domain:
          csvFile.write(field.domain)
        csvFile.write( "," )
        if not field.editable is None:
          csvFile.write(str(field.editable))
        csvFile.write( "," )
        if not field.isNullable is None:
          csvFile.write(str(field.isNullable))
        csvFile.write( "," )
        
        csvFile.write(str(field.length))
        csvFile.write( "," )
        csvFile.write(str(field.precision))
        csvFile.write( "," )
        csvFile.write(str(field.required))
        csvFile.write( "," )
        csvFile.write(str(field.scale))
        csvFile.write( "," )
        csvFile.write(field.type)
   
        csvFile.write( os.linesep )
