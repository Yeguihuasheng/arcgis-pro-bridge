# -*- coding: UTF-8 -*-

import arcpy

import os
import codecs
import datetime
#import pytz

#ツール定義
class ExtractFeatureAttachments(object):

  def __init__(self):
    self.label = "Extract Feature Attachments"
    self.description = "Extract all attached files to the specified folder."

    self.category = "DataManagement"
    self.canRunInBackground = False

  def getParameterInfo(self):

    param0 = arcpy.Parameter(
               displayName="In Records",
               name="in_table",
               datatype=["DETable", "GPTableView"],
               parameterType="Required",
               direction="Input")

    param1 = arcpy.Parameter(
        displayName="Output Folder",
        name="out_Dir",
        datatype="DEFolder",
        parameterType="Required",
        #parameterType="Derived",
        direction="Output")

    params = [param0, param1]
    return params

  
  def isLicensed(self):        
    return True

  def updateParameters(self, parameters):
    return
  
  def updateMessages(self, parameters):
    if (parameters[0]):
      inTable  = parameters[0].valueAsText
      if (inTable):
        fieldnames = [f.name.upper() for f in arcpy.ListFields(inTable)]
        if (not 'ATTACHMENTID' in  fieldnames or
            not 'REL_OBJECTID' in fieldnames or
            not 'ATT_NAME' in fieldnames or
            not 'DATA' in fieldnames):
          parameters[0].setErrorMessage('The input table is not an attachments table.')
    
    return
  
  def execute(self, parameters, messages):

    inTable  = parameters[0].valueAsText
    outDir = parameters[1].valueAsText
    
    if not os.path.exists(outDir):
      os.makedirs(outDir)

    with arcpy.da.SearchCursor(inTable, ['DATA', 'ATT_NAME', 'ATTACHMENTID', 'REL_OBJECTID']) as cursor:
      for item in cursor:
        attachment = item[0]
        filenum = "ATT" + str(item[2]) + "_"  + str(item[3]) + "_"
        filename = filenum + str(item[1])
        outFile = os.path.join(outDir, filename)
        with open(outFile, 'wb') as of:
          of.write(attachment.tobytes())

        del item
        del attachment
      del cursor

    
