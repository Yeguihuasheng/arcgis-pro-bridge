# -*- coding: UTF-8 -*-

import arcpy

import os
import codecs
import datetime
#import pytz

class TableLayerToJSON(object):

  def __init__(self):
    self.label = "Table/Layer to JSON"
    self.description = "Creates a esri JSON."

    self.category = "DataManagement"
    self.canRunInBackground = False

  def getParameterInfo(self):

    param0 = arcpy.Parameter(
               displayName="In Records",
               name="in_layer",
               datatype=["GPFeatureLayer" , "GPTableView"],
               parameterType="Required",
               direction="Input")

    param1 = arcpy.Parameter(
        displayName="Output JSON",
        name="out_JSON",
        datatype="DEFile",
        parameterType="Required",
        #parameterType="Derived",
        direction="Output")
    param1.filter.list = ['json', 'txt']

    params = [param0, param1]
    return params

  
  def isLicensed(self):        
    return True

  def updateParameters(self, parameters):
    return
  
  def updateMessages(self, parameters):
    return
  
  def execute(self, parameters, messages):

    records = parameters[0].valueAsText
    outJSON = parameters[1].valueAsText

    inDesc = arcpy.Describe(records)
    if (inDesc.dataType == "FeatureLayer"):
      arcpy.FeaturesToJSON_conversion(records, outJSON)
      return

    fieldTypeDict = { "SmallInteger":"esriFieldTypeSmallInteger", 
  "Integer":"esriFieldTypeInteger",
  "Single:":"esriFieldTypeSingle",
  "Double":"esriFieldTypeDouble",
  "String":"esriFieldTypeString",
  "Date":"esriFieldTypeDate",
  "OID":"esriFieldTypeOID",
  "Geometry":"esriFieldTypeGeometry",
  "Blob":"esriFieldTypeBlob",
  "Raster":"esriFieldTypeRaster",
  "Guid:":"esriFieldTypeGUID",
  "GlobalID":"esriFieldTypeGlobalID" }
    
    fields = arcpy.ListFields(records)
    fieldList = [field.name for field in fields]

    with arcpy.da.SearchCursor(records, fieldList) as cursor:
      with codecs.open(outJSON, 'w', 'utf-8') as jsonFile:

        jsonFile.write('{ "displayFieldName": "", ')
        jsonFile.write('"fieldAliases": {')
        lstString = []
        for field in fields:
          lstString.append( '"{}":"{}"'.format(field.name, field.aliasName) )
        jsonFile.write( ','.join(lstString) )

        jsonFile.write('},') # end fieldAliases

        jsonFile.write('"fields": [')
        for index in range(len(fields)):
          field = fields[index]
          
          jsonFile.write("{")
          jsonFile.write('"name":"{}",'.format(field.name) )
          jsonFile.write('"type":"{}",'.format(fieldTypeDict[field.type]) )
          jsonFile.write('"alias":"{}",'.format(field.aliasName) )
          jsonFile.write('"length":"{}"'.format(field.length) )               
          jsonFile.write("}")
          if (index != len(fields)-1):
            jsonFile.write(",")

        jsonFile.write('],') # end field

        jsonFile.write('"features": [')

        isFirstTime = True
        for row in cursor:
          if (isFirstTime):
            isFirstTime = False
          else:
            jsonFile.write( ',' )
            
          jsonFile.write('{ "attributes": {')
          #lstRow = []
          for index in range(len(row)):
            #lstRow.append(str(record))

            jsonFile.write( '"' )
            jsonFile.write( fields[index].name )
            jsonFile.write( '":' )
            if (fields[index].type == "String"):
              #messages.addMessage(row[index])
              jsonFile.write( '"' )
              jsonFile.write( row[index] )
              jsonFile.write( '"' )
              #lstRow.append( '"{}"'.format(row[index].encode('utf-8')))
            elif (fields[index].type == "Date"):
              EPOCH = datetime.datetime(1970, 1, 1, tzinfo = None) #tzinfo=pytz.timezone('utc'))
              epochMsec = int((row[index] - EPOCH).total_seconds() / 1000)
              jsonFile.write( str(epochMsec) )
            else:
              #lstRow.append( '{}'.format(row[index]))
              jsonFile.write( '{}'.format(row[index]) )
            if (index != len(row)-1):
              jsonFile.write( ',' )
              
          #jsonFile.write( ','.join(lstRow) )
                         
          jsonFile.write('} }')
        jsonFile.write('] }') #end features


