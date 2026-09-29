# -*- coding: utf-8 -*-

import arcpy
import csv
import os

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Utility Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [findAndReplaceWorkspacePaths, CountRecordVertice, CheckGeometry,
                      FCtoGEOMulti, ListAttDomains, ListDatasets, ListFieldName,
                      ListFieldALIASName, LongestString, TabletoGEOMulti, UniqFieldValues,
                      ListDataSourcesMXDs, ListDataSourcesFolder, UpperCase,
                      ChangeTextFieldLen, ChangeTextFieldLenBy,
                      ChangeNumetricFieldTypAndLen, ChangeFieldType, WSInventory,
                      DuplicateFieldValues, SchemaCheck, ListEmptyDataset,
                      ListLayerName, UpdateField]


class UpdateField(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Update Field based on another layer"
        self.description = "Update field based on the field from another " \
                           "layer (alternative to join and field " \
                           "calculate)"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_table = arcpy.Parameter(
            displayName="Input Dataset (feature class or shapefile)",
            name="in_table",
            datatype=['DEFeatureClass', 'DEShapefile'],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        input_join_field = arcpy.Parameter(
            displayName="Input Join Field",
            name="input_join_field",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        input_join_field.filter.list = ['Text', 'Short', 'Long', 'Float', 'Single', 'Double']
        input_join_field.parameterDependencies = [in_table.name]

        input_update_field = arcpy.Parameter(
            displayName="Input Update Field",
            name="input_update_field",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        input_update_field.filter.list = ['Text', 'Short', 'Long', 'Float', 'Single', 'Double']
        input_update_field.parameterDependencies = [in_table.name]

        join_table = arcpy.Parameter(
            displayName="Join Table",
            name="join_table",
            datatype=["GPTableView"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        join_table_field = arcpy.Parameter(
            displayName="Join Table Field",
            name="join_table_field",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        join_table_field.filter.list = ['Text', 'Short', 'Long', 'Float', 'Single', 'Double']
        join_table_field.parameterDependencies = [join_table.name]

        join_ref_field = arcpy.Parameter(
            displayName="Join Reference Field",
            name="join_ref_field",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        join_ref_field.filter.list = ['Text', 'Short', 'Long', 'Float', 'Single', 'Double']
        join_ref_field.parameterDependencies = [join_table.name]

        parameters = [in_table, input_join_field, input_update_field,
                      join_table, join_table_field, join_ref_field]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def createDict(self, fc, fields):
        """
        construct a dictionary with unique id and target field values
        Args:
            table (str): table full path.
            fields (str): list with field names
        Returns:
            vDict (dict): a dictionary with unique id key and field values
        """
        attr_dict = {}
        # loop source feature class
        with arcpy.da.SearchCursor(fc, fields) as cursor:
            for row in cursor:
                attr_dict[row[0]] = row[1]
        return attr_dict


    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.AddMessage("- create data dictionary")
        valueDict = self.createDict(parameters[3].valueAsText, [parameters[4].valueAsText,
                                                                parameters[5].valueAsText])
        # set workspace
        arcpy.AddMessage("- set workspace")
        desc = arcpy.Describe(parameters[0])
        ws = desc.path
        desc1 = arcpy.Describe(ws)
        if hasattr(desc1, "datasetType") and desc1.datasetType=='FeatureDataset':
            ws = desc1.path

        count = len(list(i for i in
                         arcpy.da.SearchCursor(desc.catalogPath, ["OBJECTID"])))

        arcpy.AddMessage("- check if the input dataset is versioned")
        if desc.isVersioned:
            # Start an edit session. Must provide the workspace.
            arcpy.AddMessage("- start an edit session")
            edit = arcpy.da.Editor(ws)

            # Edit session is started without an undo/redo stack for
            # versioned data
            #  (for second argument, use False for unversioned data)
            edit.startEditing(False, True)

            # Start an edit operation
            edit.startOperation()

            # Update a row into the table.
            arcpy.AddMessage("- update the table")
            with arcpy.da.UpdateCursor(desc.catalogPath,
                                       [parameters[1].valueAsText, parameters[2].valueAsText]) as \
                    cursor:
                ten_list = [x for x in range(10, 100, 10)]
                for counter, row in enumerate(cursor, start = 1):
                    percent = int(counter * 100 / count)
                    if percent in ten_list:
                        ten_list.remove(percent)
                        arcpy.AddMessage('{} percent complete'.format(percent))
                    if row[0] in valueDict.keys():
                        row[1] = valueDict[row[0]]
                        cursor.updateRow(row)
                del row, cursor

            # Stop the edit operation.
            edit.stopOperation()

            # Stop the edit session and save the changes
            arcpy.AddMessage("- stop the edit session and save the changes")
            edit.stopEditing(True)

        else:
            # Update a row into the table.
            arcpy.AddMessage("- update the table")
            with arcpy.da.UpdateCursor(desc.catalogPath,
                                       [parameters[1].valueAsText, parameters[2].valueAsText]) as \
                    cursor:
                ten_list = [x for x in range(10, 100, 10)]
                for counter, row in enumerate(cursor, start = 1):
                    percent = int(counter * 100 / count)
                    if percent in ten_list:
                        ten_list.remove(percent)
                        arcpy.AddMessage('{} percent complete'.format(percent))
                    if row[0] in valueDict.keys():
                        row[1] = valueDict[row[0]]
                        cursor.updateRow(row)
                del row, cursor


class ListLayerName(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Layer Name"
        self.description = "Print Layer Name in Current Map Project (aprx)"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        return

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        for m in aprx.listMaps():
            print("Map: {0} Layers".format(m.name))
            for lyr in m.listLayers():
                if lyr.supports("dataSource"):
                    arcpy.AddMessage("  " + lyr.name)
        del aprx


class ListEmptyDataset(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Empty Dataset"
        self.description = "Print Empty Dataset Name in Workspace (Personal Geodatabase, File Geodatabase, and SDE)"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_ws = arcpy.Parameter(
            displayName="Workspace",
            name="in_ws",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        in_datatype = arcpy.Parameter(
            displayName="Dataset Type",
            name="in_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        in_datatype.filter.list = ['FeatureClass', 'Table']

        parameters = [in_ws, in_datatype]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def inventory_data(self, workspace, datatype):
        """
        Generates full path names under a catalog tree for all requested
        datatype(s).

        Parameters:
        workspace: string
            The top-level workspace that will be used.
        datatypes: string | list | tuple
            Keyword(s) representing the desired datatypes. A single
            datatype can be expressed as a string, otherwise use
            a list or tuple. See arcpy.da.Walk documentation
            for a full list.
        """
        for path, path_names, data_names in arcpy.da.Walk(workspace,
                                                          datatype = datatype):
            for data_name in data_names:
                yield os.path.join(path, data_name)

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_wspace = parameters[0].valueAsText
        in_dtype = parameters[1].valueAsText
        iList = list(self.inventory_data(in_wspace, in_dtype))
        # loop data list
        counter = 1
        for dataset in iList:
            arcpy.AddMessage("{} of {}".format(counter, len(iList)))
            result = arcpy.GetCount_management(dataset)
            if result == 0:
                arcpy.AddMessage("{}".format(dataset))
            counter += 1


class findAndReplaceWorkspacePaths(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find and Replace Workspace Paths"
        self.description = "Find and Replace Workspace Paths"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_mxds = arcpy.Parameter(
            displayName="Input MXDs",
            name="in_mxds",
            datatype="DEMapDocument",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        findwspath = arcpy.Parameter(
            displayName="Old Workspace Path",
            name="findwspath",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        replacewspath = arcpy.Parameter(
            displayName="New Workspace Path",
            name="replacewspath",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        parameters = [in_mxds, findwspath, replacewspath]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        inMXDs = parameters[0].valueAsText.split(';')
        findworkspacepath = parameters[1].valueAsText
        replaceworkspacepath = parameters[2].valueAsText
        for counter, inMXD in enumerate(inMXDs, start=1):
            inMXD = inMXD.replace("'", "")
            arcpy.AddMessage('\n# {} of {}: {}'.format(
                counter, len(inMXDs), inMXD))
            mxd = arcpy.mapping.MapDocument(inMXD)
            mxd.findAndReplaceWorkspacePaths(findworkspacepath, replaceworkspacepath)
            mxd.save()
            del mxd
        return


class CountRecordVertice(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Count Records and Vertices"
        self.description = "Print number of records and vertices"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_features = arcpy.Parameter(
            displayName="Input Feature Classes",
            name="in_feature",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        in_features.filter.list = ["Polyline", "POLYGON"]

        parameters = [in_features]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        inFeatures = parameters[0].valueAsText.split(';')
        for counter, inFeature in enumerate(inFeatures, start=1):
            inFeature = inFeature.replace("'", "")
            arcpy.AddMessage('\n# {} of {}: {}'.format(
                counter, len(inFeatures), inFeature))
            numberrecords = int(
                arcpy.GetCount_management(inFeature).getOutput(0))
            with arcpy.da.SearchCursor(inFeature, "SHAPE@") as cursor:
                totVert = 0
                for row in cursor:
                    totVert += row[0].pointCount
            arcpy.AddMessage('    - Total number of records: {}'.format(
                '{0:,}'.format(numberrecords)))
            arcpy.AddMessage('    - Total number of vertices: {}\n'.format(
                '{0:,}'.format(totVert)))
        return


class CheckGeometry(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Check Geomtry"
        self.description = "Check geometry and print out the result"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_features = arcpy.Parameter(
            displayName="Input Feature Classes",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        parameters = [in_features]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        inFeatures = parameters[0].valueAsText.split(";")
        for counter, inFeature in enumerate(inFeatures, start=1):
            inFeature = inFeature.replace("'", "")
            arcpy.AddMessage('\n# {} of {}: {}'.format(
                counter, len(inFeatures), inFeature))
            ws = arcpy.env.scratchGDB
            arcpy.env.workspace = ws
            arcpy.env.overwriteOutput = True
            temp_table = "temp_table"
            arcpy.CheckGeometry_management(inFeature, temp_table)
            values = [row for row in arcpy.da.SearchCursor(temp_table, "*")]
            if values:
                arcpy.AddMessage("   - Geometry problems found")
                for i in values:
                    arcpy.AddMessage(
                        "     OID:{:<10d}:   {:35s}".format(i[2], i[3]))
            else:
                arcpy.AddMessage("   - No Geometry problems found")
        arcpy.AddMessage("\n")
        return


class FCtoGEOMulti(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "FCs to Geodatabase GP Off"
        self.description = "Feature Classes to Geodatabase with Geoprocessing History Off"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_features = arcpy.Parameter(
            displayName="Input Feature Classes",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        in_ws = arcpy.Parameter(
            displayName="Workspace",
            name="in_ws",
            datatype=["DEWorkspace","DEFeatureDataset"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        parameters = [in_features, in_ws]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # disable geoprocessing history logging
        arcpy.SetLogHistory(False)
        arcpy.env.workspace = parameters[1].valueAsText
        arcpy.env.overwriteOutput = True

        # Execute FeatureClassToGeodatabase
        arcpy.FeatureClassToGeodatabase_conversion(parameters[0].valueAsText,
                                                   parameters[1].valueAsText)
        return


class ListAttDomains(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Domains"
        self.description = "Print out attribute domains"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_datasets = arcpy.Parameter(
            displayName="Input Datasets",
            name="in_datasets",
            datatype=["GPFeatureLayer", "DETable"],
            parameterType="Required",
            direction="Input",
            multiValue=True)

        in_ws = arcpy.Parameter(
            displayName="Workspace",
            name="in_ws",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        in_ws.filter.list = ['LocalDatabase', 'RemoteDatabase']

        parameters = [in_datasets, in_ws]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def codeddomainDict(self, workspace):
        """
        construct a dictionary with attribute domain code value and code desc

        Args:
            ws (str): workspace

        Returns:
            coded_dict (dict): a dictionary with code value and code desc
        """
        arcpy.env.workspace = workspace

        # dictionary - {domain name lowercase: {code value: code desc}}
        coded_dict = {}
        domains = arcpy.da.ListDomains(workspace)
        for domain in domains:
            # meta.arcpy.AddMessage('Domain name : {0}'.format(domain.name))
            if domain.domainType == 'CodedValue':
                coded_values = domain.codedValues
                temp_dict = {}
                for val, desc in coded_values.items():
                    # meta.arcpy.AddMessage('{0} : {1}'.format(val, desc))
                    temp_dict[val] = desc
                coded_dict[domain.name.lower()] = temp_dict
            elif domain.domainType == 'Range':
                temp_dict = {}
                temp_dict['min'] = domain.range[0]
                temp_dict['max'] = domain.range[1]
                coded_dict[domain.name.lower()] = temp_dict

        return coded_dict

    def execute(self, parameters, messages):
        """The source code of the tool."""
        input_datasets = parameters[0].valueAsText.split(';')
        wspace = parameters[1].valueAsText

        arcpy.env.workspace = wspace
        domaindicts = self.codeddomainDict(wspace)

        for counter, dataset in enumerate(input_datasets, start=1):
            dataset = dataset.replace("'", "")
            desc = arcpy.Describe(dataset)
            arcpy.AddMessage(("\n# {} of {} : {}".format(counter, len(
                input_datasets), desc.baseName)))

            fields = arcpy.ListFields(dataset)
            # dictionary - {field name lowercase: domain name lowercase}
            fieldswithdomain = {field.name.lower(): field.domain.lower()
                                for field in fields if
                                field.domain != ""}
            # all attribute elements
            for counter1, field in enumerate(fieldswithdomain):
                if counter1 > 0:
                    arcpy.AddMessage("  ")
                arcpy.AddMessage("    - field name : {}".format(field))
                arcpy.AddMessage("    - domain name: {}".format(
                    fieldswithdomain[field]))
                domaincodelist = domaindicts[fieldswithdomain[field]]
                for ecodeddomain in domaincodelist.keys():
                    arcpy.AddMessage(
                        "                 {} : {}".format(ecodeddomain,
                                                          domaincodelist[
                                                              ecodeddomain]))
        arcpy.AddMessage("  ")
        return


class ListDatasets(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Datasets"
        self.description = "Print datasets in workspace"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_ws = arcpy.Parameter(
            displayName="Workspace",
            name="in_ws",
            datatype=["DEWorkspace","DEFeatureDataset"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        parameters = [in_ws]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def codeddomainDict(self, workspace):
        """
        construct a dictionary with attribute domain code value and code desc

        Args:
            ws (str): workspace

        Returns:
            coded_dict (dict): a dictionary with code value and code desc
        """
        arcpy.env.workspace = workspace

        # dictionary - {domain name lowercase: {code value: code desc}}
        coded_dict = {}
        domains = arcpy.da.ListDomains(workspace)
        for domain in domains:
            # meta.arcpy.AddMessage('Domain name : {0}'.format(domain.name))
            if domain.domainType == 'CodedValue':
                coded_values = domain.codedValues
                temp_dict = {}
                for val, desc in coded_values.items():
                    # meta.arcpy.AddMessage('{0} : {1}'.format(val, desc))
                    temp_dict[val] = desc
                coded_dict[domain.name.lower()] = temp_dict
            elif domain.domainType == 'Range':
                temp_dict = {}
                temp_dict['min'] = domain.range[0]
                temp_dict['max'] = domain.range[1]
                coded_dict[domain.name.lower()] = temp_dict

        return coded_dict

    def execute(self, parameters, messages):
        """The source code of the tool."""
        walk = arcpy.da.Walk(parameters[0].valueAsText)
        filenamelist = []
        for dirpath, dirnames, filenames in walk:
            for filen in filenames:
                filenamelist.append(filen)

        arcpy.AddMessage("\n")
        for filename in sorted(filenamelist):
            arcpy.AddMessage("{}".format(filename))
        arcpy.AddMessage("\n")
        return


class ListFieldName(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Field Names"
        self.description = "Print out field names in Tables and Feature Classes"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_tables = arcpy.Parameter(
            displayName="Input Tables",
            name="in_tables",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        parameters = [in_tables]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_tables = parameters[0].valueAsText.split(";")
        for counter, intable in enumerate(in_tables, start=1):
            intable = intable.replace("'", "")
            arcpy.AddMessage('\n# {} of {}: {}'.format(
                counter, len(in_tables), intable))
            for field in arcpy.ListFields(intable):
                arcpy.AddMessage(field.baseName)
        arcpy.AddMessage("\n")
        return


class ListFieldALIASName(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Field and Alias Names"
        self.description = "Print out field and Alias names in Tables and Feature Classes"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_tables = arcpy.Parameter(
            displayName="Input Tables",
            name="in_tables",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        parameters = [in_tables]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_tables = parameters[0].valueAsText.split(";")
        for counter, intable in enumerate(in_tables, start=1):
            intable = intable.replace("'", "")
            arcpy.AddMessage('\n# {} of {}: {}'.format(
                counter, len(in_tables), intable))
            for field in arcpy.ListFields(intable):
                arcpy.AddMessage('{}, {}'.format(field.baseName, field.aliasName))
        arcpy.AddMessage("\n")
        return


class LongestString(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Longest String"
        self.description = "List the longest string in Tables and Feature Classes"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_tables = arcpy.Parameter(
            displayName="Input Tables",
            name="in_tables",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        parameters = [in_tables]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_tables = parameters[0].valueAsText.split(";")
        for counter, intable in enumerate(in_tables, start=1):
            intable = intable.replace("'", "")
            arcpy.AddMessage('\n# {} of {}: {}'.format(
                counter, len(in_tables), intable))
            fieldnames = [field.baseName for field in
                          arcpy.ListFields(intable, field_type='String')]
            for counter, fieldname in enumerate(fieldnames):
                arcpy.AddMessage(
                    "{} of {}: {}".format(counter + 1, len(fieldnames),
                                          fieldname))
                with arcpy.da.SearchCursor(intable, fieldname) as cursor:
                    fieldvalue_list = [row[0] for row in cursor if
                                       row[0] is not None]
                if fieldvalue_list:
                    arcpy.AddMessage("    longest string: {}".format(
                        len(max(fieldvalue_list, key=len))))
                    arcpy.AddMessage("    {}".format(
                        max(fieldvalue_list, key=len).encode(
                            'utf-8').decode('utf-8', 'ignore')))  # add encode to fix unicode error
                else:
                    arcpy.AddMessage("    EMPTY FIELD")
        arcpy.AddMessage("\n")
        return


class TabletoGEOMulti(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Tables to Geodatabase GP Off"
        self.description = "Tables to Geodatabase with Geoprocessing History Off"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_tables = arcpy.Parameter(
            displayName="Input Tables",
            name="in_tables",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        in_ws = arcpy.Parameter(
            displayName="Workspace",
            name="in_ws",
            datatype=["DEWorkspace","DEFeatureDataset"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        parameters = [in_tables, in_ws]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # disable geoprocessing history logging
        arcpy.SetLogHistory(False)
        arcpy.env.workspace = parameters[1].valueAsText
        arcpy.env.overwriteOutput = True

        # Execute FeatureClassToGeodatabase
        arcpy.TableToGeodatabase_conversion(parameters[0].valueAsText,
                                                   parameters[1].valueAsText)
        return


class UniqFieldValues(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Unique Field Values"
        self.description = "Print unique field values"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_table = arcpy.Parameter(
            displayName="Input Table",
            name="in_table",
            datatype=["GPTableView"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        in_fields = arcpy.Parameter(
            displayName="Fields",
            name="in_fields",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        in_fields.filter.list = ['Text', 'Short', 'Long', 'Float', 'Single', 'Double']
        in_fields.parameterDependencies = [in_table.name]

        parameters = [in_table, in_fields]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def constructDict(self, table, fields):
        """
        construct a dictionary with table name and field values

        Args:
            table (str): table full path.
            fields (str): field names, separated by ';'

        Returns:
            vDict (dict): a dictionary with field name key and field values
        """
        vDict = dict((fname, []) for fname in fields)
        with arcpy.da.SearchCursor(table, fields) as cursor:
            for row in cursor:
                for i in range(len(row)):
                    # can't sort None in python 3, replace None to ""
                    if row[i]:
                        vDict[fields[i]].append(row[i])
                    else:
                        vDict[fields[i]].append("")
        return vDict

    def execute(self, parameters, messages):
        """The source code of the tool."""
        fieldList = parameters[1].valueAsText.split(";")
        valueDict = self.constructDict(parameters[0].valueAsText, fieldList)
        for fname in valueDict:
            arcpy.AddMessage("\nField: {}".format(fname))
            arcpy.AddMessage("unique:")
            occurances = valueDict[fname]
            for i in sorted(set(occurances)):
                icount = occurances.count(i)
                if i is None:
                    arcpy.AddMessage("    None: 0")
                elif isinstance(i, str):
                    arcpy.AddMessage(
                        "    {}: {}".format(i.encode('utf-8').decode('utf-8', 'ignore'), icount))
                else:
                    arcpy.AddMessage("    {}: {}".format(i, icount))
        arcpy.AddMessage("    ")
        return


class ListDataSourcesMXDs(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Data Sources MXDs"
        self.description = "List layer's data source from MXDs"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_mxds = arcpy.Parameter(
            displayName="Input MXDs",
            name="in_mxds",
            datatype="DEFile",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        in_mxds.filter.list = ['mxd']

        out_csv = arcpy.Parameter(
            displayName="Output CSV File",
            name="out_csv",
            datatype="DEFile",
            parameterType="Required",
            direction="Output",
            multiValue=False)
        out_csv.filter.list = ['csv']
        parameters = [in_mxds, out_csv]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def crawlmxds(self, in_mxds):
        for counter, in_mxd in enumerate(in_mxds, start=1):
            # when mxd file name has a space, arcgis input add "'" and need to remove it
            in_mxd = in_mxd.strip("'")
            arcpy.AddMessage("\n#{} of {}: {}".format(counter, len(in_mxds), in_mxd))
            mxd = arcpy.mapping.MapDocument(in_mxd)
            dataframes = arcpy.mapping.ListDataFrames(mxd)
            for df in dataframes:
                dfDesc = df.description if df.description != "" else "None"
                layers = arcpy.mapping.ListLayers(mxd, "", df)
                for lyr in layers:
                    lyrName = lyr.name
                    lyrDatasource = lyr.dataSource if lyr.supports(
                        "dataSource") else "N/A"
                    seq = (in_mxd, df.name, dfDesc, lyrName, lyrDatasource);
                    yield seq
            del mxd

    def execute(self, parameters, messages):
        """The source code of the tool."""
        inMXDs = parameters[0].valueAsText.split(";")
        outCSV = parameters[1].valueAsText
        with open(outCSV, "wb") as f:
            w = csv.writer(f)
            header = ("MXD Path", "DataFrame Name", "DataFrame Description",
                      "Layer name", "Layer Datasource")
            w.writerow(header)
            rows = self.crawlmxds(inMXDs)
            w.writerows(rows)
        arcpy.AddMessage("\n")
        return


class ListDataSourcesFolder(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Data Sources MXDs in a Folder"
        self.description = "List layer's data source from MXDs in a folder"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_folder = arcpy.Parameter(
            displayName="Input Folder",
            name="in_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        out_csv = arcpy.Parameter(
            displayName="Output CSV File",
            name="out_csv",
            datatype="DEFile",
            parameterType="Required",
            direction="Output",
            multiValue=False)
        out_csv.filter.list = ['csv']
        parameters = [in_folder, out_csv]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def crawlmxds(self, inFolder):
        for root, dirs, files in os.walk(inFolder):
            for counter, f in enumerate(files, start=1):
                if f.lower().endswith(".mxd"):
                    mxdName = os.path.splitext(f)[0]
                    arcpy.AddMessage("\n#{} of {}: {}".format(counter, len(files), mxdName))
                    mxdPath = os.path.join(root, f)
                    mxd = arcpy.mapping.MapDocument(mxdPath)
                    dataframes = arcpy.mapping.ListDataFrames(mxd)
                    for df in dataframes:
                        dfDesc = df.description if df.description != "" else "None"
                        layers = arcpy.mapping.ListLayers(mxd, "", df)
                        for lyr in layers:
                            lyrName = lyr.name
                            lyrDatasource = lyr.dataSource if lyr.supports(
                                "dataSource") else "N/A"
                            seq = (mxdName, mxdPath, df.name, dfDesc, lyrName,
                                   lyrDatasource);
                            yield seq
                    del mxd

    def execute(self, parameters, messages):
        """The source code of the tool."""
        inFolder = parameters[0].valueAsText
        outCSV = parameters[1].valueAsText
        with open(outCSV, "wb") as f:
            w = csv.writer(f)
            header = ("Map Document", "MXD Path", "DataFrame Name",
                      "DataFrame Description", "Layer name", "Layer Datasource")
            w.writerow(header)
            rows = self.crawlmxds(inFolder)
            w.writerows(rows)
        arcpy.AddMessage("\n")
        return


class UpperCase(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Field Name To Upper Case"
        self.description = "Change field name to all upper case"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_table = arcpy.Parameter(
            displayName="Input Table",
            name="in_table",
            datatype=["GPFeatureLayer", "DETable"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        out_ws = arcpy.Parameter(
            displayName="Output Location",
            name="out_ws",
            datatype=["DEWorkspace", "DEFeatureDataset"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        out_table = arcpy.Parameter(
            displayName="Output Table Name",
            name="out_table",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        parameters = [in_table, out_ws, out_table]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        listFields = arcpy.ListFields(parameters[0].valueAsText)

        fms = arcpy.FieldMappings()
        for i in listFields:
            if i.type not in ["OID", "Geometry", "GlobalID", "Guid"]:
                # https://geonet.esri.com/thread/159184
                fm = arcpy.FieldMap()
                fm.addInputField(parameters[0].valueAsText, i.name)
                newField = fm.outputField
                newField.name = i.name.upper()
                fm.outputField = newField
                fms.addFieldMap(fm)

        desc = arcpy.Describe(parameters[0].valueAsText)
        if desc.dataType == "FeatureClass":
            arcpy.FeatureClassToFeatureClass_conversion(parameters[0].valueAsText, parameters[1].valueAsText, parameters[2].valueAsText, field_mapping=fms)
        elif desc.dataType == "Table":
            arcpy.TableToTable_conversion(parameters[0].valueAsText, parameters[
                1].valueAsText, parameters[2].valueAsText, field_mapping=fms)
        arcpy.AddMessage("  ")
        return


class ChangeTextFieldLen(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Change Text Field Length"
        self.description = "Change Text Field Length"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_table = arcpy.Parameter(
            displayName="Input Table",
            name="in_table",
            datatype=["GPTableView"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        in_fields = arcpy.Parameter(
            displayName="Fields",
            name="in_fields",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        in_fields.filter.list = ['Text']
        in_fields.parameterDependencies = [in_table.name]

        in_len = arcpy.Parameter(
            displayName="Field Length",
            name="in_len",
            datatype="GPLong",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        parameters = [in_table, in_fields, in_len]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[2].valueAsText:
            with arcpy.da.SearchCursor(parameters[0].valueAsText, parameters[1].valueAsText) as cursor:
                fieldvalue_list = [row[0] for row in cursor if row[0] is not None]
            if fieldvalue_list:
                if int(parameters[2].valueAsText) < len(max(fieldvalue_list, key=len)):
                    parameters[2].setErrorMessage("New field length is smaller than the longest string ({}) in the field.".format(str(len(max(fieldvalue_list, key=len)))))
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # set list of OID and target field
        replace_fields = ['OID@', parameters[1].valueAsText]
        # dictionary of OID and target field value
        valueDict = {r[0]: r[1] for r in arcpy.da.SearchCursor(parameters[0].valueAsText, replace_fields)}
        # update cursor
        with arcpy.da.UpdateCursor(parameters[0].valueAsText, replace_fields) as cursor:
            arcpy.AddMessage("\n    delete {} field".format(parameters[1].valueAsText))
            arcpy.DeleteField_management(parameters[0].valueAsText, parameters[1].valueAsText)
            arcpy.AddMessage("    add {} field".format(parameters[1].valueAsText))
            arcpy.AddField_management(parameters[0].valueAsText, parameters[1].valueAsText, field_type='TEXT', field_length=int(parameters[2].valueAsText))
            arcpy.AddMessage("    update field value")
            for row in cursor:
                # set value to the new field
                row[1] = valueDict[row[0]]
                cursor.updateRow(row)

        arcpy.AddMessage("\n")
        return


class ChangeTextFieldLenBy(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Change Text Field Length By"
        self.description = "Change Text Field Length multiply the longest string in the field by the input number"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_table = arcpy.Parameter(
            displayName="Input Table",
            name="in_table",
            datatype=["GPTableView"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        in_fields = arcpy.Parameter(
            displayName="Fields",
            name="in_fields",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        in_fields.filter.list = ['Text']
        in_fields.parameterDependencies = [in_table.name]

        in_len = arcpy.Parameter(
            displayName="Field Length Increase By (ex 1.2)",
            name="in_len",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        in_len.value = 1.2

        parameters = [in_table, in_fields, in_len]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        fieldnames = parameters[1].valueAsText.split(";")
        for counter, fname in enumerate(fieldnames, start=1):
            arcpy.AddMessage("\n{} of {}: {}".format(counter, len(fieldnames), fname))
            # set list of OID and target field
            replace_fields = ['OID@', fname]
            # dictionary of OID and target field value
            valueDict = {}
            fieldvaluelist = []
            with arcpy.da.SearchCursor(parameters[0].valueAsText, replace_fields) as cursor:
                for row in cursor:
                    valueDict[row[0]] = row[1]
                    if row[1] is not None:
                        fieldvaluelist.append(row[1])
            if fieldvaluelist:
                fldlength = int(len(max(fieldvaluelist, key=len))*parameters[2].value)
            else:
                fldlength = 25
            # update cursor
            with arcpy.da.UpdateCursor(parameters[0].valueAsText, replace_fields) as cursor:
                arcpy.AddMessage("    delete {} field".format(fname))
                arcpy.DeleteField_management(parameters[0].valueAsText, fname)
                arcpy.AddMessage("    add {} field".format(fname))
                arcpy.AddField_management(parameters[0].valueAsText, fname, field_type='TEXT', field_length=fldlength)
                arcpy.AddMessage("    update field value")
                for row in cursor:
                    # set value to the new field
                    row[1] = valueDict[row[0]]
                    cursor.updateRow(row)
        arcpy.AddMessage("\n")
        return


class ChangeNumetricFieldTypAndLen(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Change Numeric Field Type and Len"
        self.description = "Change Numeric Field Type and Length. THE SCRIPT DOESN'T CHECK VALUE LENGHT."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_table = arcpy.Parameter(
            displayName="Input Table",
            name="in_table",
            datatype=["GPTableView"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        in_fields = arcpy.Parameter(
            displayName="Fields",
            name="in_fields",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        in_fields.filter.list = ['Short', 'Long', 'Float', 'Single', 'Double']
        in_fields.parameterDependencies = [in_table.name]

        in_type = arcpy.Parameter(
            displayName="New Field Type",
            name="in_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        in_type.filter.list = ['SHORT', 'LONG', 'DOUBLE', 'FLOAT']

        in_len = arcpy.Parameter(
            displayName="Field Length",
            name="in_len",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input",
            multiValue=False)

        parameters = [in_table, in_fields, in_type, in_len]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # set list of OID and target field
        replace_fields = ['OID@', parameters[1].valueAsText]
        # dictionary of OID and target field value
        valueDict = {r[0]: r[1] for r in arcpy.da.SearchCursor(parameters[0].valueAsText, replace_fields)}
        # update cursor
        with arcpy.da.UpdateCursor(parameters[0].valueAsText, replace_fields) as cursor:
            arcpy.AddMessage("\n    delete {} field".format(parameters[1].valueAsText))
            arcpy.DeleteField_management(parameters[0].valueAsText, parameters[1].valueAsText)
            arcpy.AddMessage("    add {} field".format(parameters[1].valueAsText))
            if parameters[3].valueAsText:
                arcpy.AddField_management(parameters[0].valueAsText, parameters[1].valueAsText, field_type=parameters[2].valueAsText, field_length=int(parameters[3].valueAsText))
            else:
                arcpy.AddField_management(parameters[0].valueAsText, parameters[1].valueAsText,field_type=parameters[2].valueAsText)
            arcpy.AddMessage("    update field value")
            for row in cursor:
                # set value to the new field
                row[1] = valueDict[row[0]]
                cursor.updateRow(row)
        arcpy.AddMessage("\n")
        return


class ChangeFieldType(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Change Field Type"
        self.description = "Change Field Type"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_table = arcpy.Parameter(
            displayName="Input Table",
            name="in_table",
            datatype=["GPTableView"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        in_fields = arcpy.Parameter(
            displayName="Fields",
            name="in_fields",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        in_fields.filter.list = ['Text', 'Short', 'Long', 'Float', 'Single', 'Double']
        in_fields.parameterDependencies = [in_table.name]

        in_type = arcpy.Parameter(
            displayName="New Field Type",
            name="in_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        paras = [in_table, in_fields, in_type]

        return paras

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, paras):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        typelist = paras[2].filter
        if paras[1].valueAsText:
            fields = [field for field in (arcpy.ListFields(paras[0].valueAsText))]
            for field in fields:
                if field.name == paras[1].valueAsText:
                    if field.type == 'String':
                        typelist.list = ['SHORT', 'LONG', 'DOUBLE', 'FLOAT']
                    else:
                        typelist.list = ['STRING']
        return

    def updateMessages(self, paras):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def is_digit(self,s):
        """
        check the list and return if all values are numeber
        https://stackoverflow.com/questions/354038/how-do-i-check-if-a-string-is-a-number-float
        :param s: list
        :return:
        """
        for textvalue in s:
            try:
                float(textvalue)
            except ValueError:
                arcpy.AddMessage("\n*******************************************")
                arcpy.AddMessage("    Text contain non-numeric value: {}".format(textvalue))
                self.getkey(textvalue)
                exit()

    def valuelen(self, fieldvalue_list):
        """
        convert numberic list to string list and return max length
        :param fieldvalue_list: list
        :return: max length
        """
        fieldvalue_list = list(map(str, fieldvalue_list))
        return len(max(fieldvalue_list, key=len))

    def getkey(self, textvalue):
        for oid, tvalue in valueDict.items():
            if tvalue == textvalue:
                arcpy.AddMessage("\n    OBJECT ID: {}    ".format(oid))

    def execute(self, paras, messages):
        """The source code of the tool."""
        tableflist = arcpy.ListFields(paras[0].valueAsText)
        for tablefield in tableflist:
            if tablefield.name == paras[1].valueAsText:
                oldftype = tablefield.type
                break

        arcpy.AddMessage("\n# {}: CONVERTING {} TO {}".format(paras[1].valueAsText, oldftype.upper(), paras[2].valueAsText))

        # set list of OID and target field
        replace_fields = ['OID@', paras[1].valueAsText]

        # dictionary of OID and target field values
        global valueDict
        valueDict= {}
        # list of OID and target field values
        fieldvaluelist = []
        with arcpy.da.SearchCursor(paras[0].valueAsText, replace_fields) as cursor:
            for row in cursor:
                valueDict[row[0]] = row[1]
                # remove Null values
                if row[1] is not None and row[1] != '':
                    fieldvaluelist.append(row[1])

        # if new field type is SHORT, LONG, DOUBLE, FLOAT
        if paras[2].valueAsText != 'STRING':
            # check input string value can be converted to int (short or long)
            if fieldvaluelist:
                self.is_digit(fieldvaluelist)
        else:
            fldlength = int(self.valuelen(fieldvaluelist)*1.3)

        with arcpy.da.UpdateCursor(paras[0].valueAsText, replace_fields) as cursor:
            arcpy.AddMessage("    - deleting field".format(paras[1].valueAsText))
            arcpy.DeleteField_management(paras[0].valueAsText, paras[1].valueAsText)
            arcpy.AddMessage("    - adding field".format(paras[1].valueAsText))
            if paras[2].valueAsText == 'STRING':
                arcpy.AddField_management(paras[0].valueAsText, paras[1].valueAsText, field_type=paras[2].valueAsText, field_length=int(fldlength))
            else:
                arcpy.AddField_management(paras[0].valueAsText, paras[1].valueAsText, field_type=paras[2].valueAsText)
            arcpy.AddMessage("    - updating field values")

            fieldtype = paras[2].value
            for row in cursor:
                # set value to the new field
                if valueDict[row[0]]:
                    # From String to Short or Long
                    if (fieldtype == 'SHORT') or (fieldtype == 'LONG'):
                        row[1] = int(valueDict[row[0]])
                    # From String to double or float
                    elif (fieldtype == 'DOUBLE') or (fieldtype == 'FLOAT'):
                        row[1] = float(valueDict[row[0]])
                    elif fieldtype == 'STRING':
                        row[1] = str(valueDict[row[0]]).split(".")[0]
                else:
                    row[1] = None

                cursor.updateRow(row)

        arcpy.AddMessage("\n")
        return


class WSInventory(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Workspace Data Inventory to CSV"
        self.description = "Create CSV file with inventory (full path, feature dataset name, dataset name, shape type) of Workspace (Personal Geodatabase, File Geodatabase, and SDE)"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_ws = arcpy.Parameter(
            displayName="Workspace",
            name="in_ws",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        out_csv = arcpy.Parameter(
            displayName="Output CSV File",
            name="out_csv",
            datatype="DEFile",
            parameterType="Required",
            direction="Output",
            multiValue=False)
        out_csv.filter.list = ['csv']
        parameters = [in_ws, out_csv]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def inventory_data(self, workspace, datatypes):
        """
        Generates full path names under a catalog tree for all requested
        datatype(s).

        Parameters:
        workspace: string
            The top-level workspace that will be used.
        datatypes: string | list | tuple
            Keyword(s) representing the desired datatypes. A single
            datatype can be expressed as a string, otherwise use
            a list or tuple. See arcpy.da.Walk documentation
            for a full list.
        """
        for path, path_names, data_names in arcpy.da.Walk(workspace, datatype=datatypes):
            for data_name in data_names:
                yield os.path.join(path, data_name)

    def crawldb(self, input_workspace):
        """
        Generates iterator of full path, feature dataset name, dataset name, shape type for every dataset in workspace.

        Parameters:
        workspace: string
            The top-level workspace that will be used.
        """
        # loop data list
        for dataset in self.inventory_data(input_workspace, "Any"):
            # check if data is accessable/readable
            if arcpy.Exists(dataset):
                # Create a Describe object
                desc = arcpy.Describe(dataset)
                # dataset name
                dataset_basename = desc.baseName
                # dataset type
                dataset_type = desc.dataType
                # if dataset is feature class
                if dataset_type == "FeatureClass":
                    # fc path
                    fcHome = os.path.dirname(dataset)
                    # if feature class is inside feature dataset
                    if arcpy.Describe(fcHome).dataType == "FeatureDataset":
                        # return feature dataset name
                        dataset_featuredataset = os.path.basename(fcHome)
                    else:
                        dataset_featuredataset = ""
                    # dataset shape type
                    dataset_shape = desc.shapeType
                else:
                    dataset_shape = ""
                    dataset_featuredataset = ""
                # create tuple
                seq = (dataset, dataset_featuredataset, dataset_basename, dataset_type, dataset_shape)
                yield seq

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_wspace = parameters[0].valueAsText
        arcpy.AddMessage("{}".format(in_wspace))
        out_csv = parameters[1].valueAsText
        with open(out_csv, 'wb') as f:
            # set csv writer object
            w = csv.writer(f)
            # set csv header
            header = ("Source", "FeatureDataset", "TableName", "DatasetType", "ShapeType")

            w.writerow(header)
            rows = self.crawldb(in_wspace)
            for i in rows:
                w.writerow(i)

        return


class DuplicateFieldValues(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "List Duplicate Field Values"
        self.description = "Print duplicate field values"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_table = arcpy.Parameter(
            displayName="Input Table",
            name="in_table",
            datatype=["GPTableView"],
            parameterType="Required",
            direction="Input",
            multiValue=False)

        in_fields = arcpy.Parameter(
            displayName="Fields",
            name="in_fields",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        in_fields.filter.list = ['Text', 'Short', 'Long', 'Float', 'Single', 'Double']
        in_fields.parameterDependencies = [in_table.name]

        parameters = [in_table, in_fields]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def constructDict(self, table, fields):
        """
        construct a dictionary with table name and field values

        Args:
            table (str): table full path.
            fields (str): field names, separated by ';'

        Returns:
            vDict (dict): a dictionary with field name key and field values
        """
        vDict = dict((fname, []) for fname in fields)
        with arcpy.da.SearchCursor(table, fields) as cursor:
            for row in cursor:
                for i in range(len(row)):
                    vDict[fields[i]].append(row[i])
        return vDict

    def execute(self, parameters, messages):
        """The source code of the tool."""
        fieldList = parameters[1].valueAsText.split(";")
        valueDict = self.constructDict(parameters[0].valueAsText, fieldList)
        for fname in valueDict:
            arcpy.AddMessage("\nField: {}".format(fname))
            arcpy.AddMessage("duplicate:")
            occurances = valueDict[fname]
            for i in sorted(set(occurances)):
                icount = occurances.count(i)
                if icount > 1:
                    if i is None:
                        arcpy.AddMessage("    None/Null: 0")
                    elif isinstance(i, str):
                        arcpy.AddMessage(
                            "    {}: {}".format(i.encode('utf-8').decode('utf-8', 'ignore'), icount))
                    else:
                        arcpy.AddMessage("    {}: {}".format(i, icount))
        arcpy.AddMessage("    ")
        return


class SchemaCheck(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Check Schema"
        self.description = "Check schema between two datasets"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Features parameter
        in_tables = arcpy.Parameter(
            displayName="Input Tables",
            name="in_tables",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        target_tables = arcpy.Parameter(
            displayName="Target Tables",
            name="target_tables",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input",
            multiValue=False)

        parameters = [in_tables, target_tables]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def compareIntersect(self, x, y):
        return frozenset(x).intersection(y)

    def compareDifference(self, x, y):
        return frozenset(x).difference(y)

    def makeFieldDict(self, input_layer):
        lFields = arcpy.ListFields(input_layer)

        fieldDict = dict()
        for lf in lFields:
            # change filenames to lower case
            fieldDict[lf.name.lower()] = [lf.type, lf.length]
        return fieldDict

    def baseName(self, input_layer, target_layer):
        """
        return input and target data basename.
        Parameters:
        input_layer: string
            input data full path. ex) C:\\Works\\GEODB\Data.gdb\\PublicPt
        target_layer: string
            target data full path. ex) Database Connections\\Connection to
            SDE.sde\\SDE.PublicPt
        """
        if ".sde" in input_layer:
            # remove schema from name
            in_name = arcpy.Describe(input_layer).baseName.split(".")[1]
        else:
            in_name = arcpy.Describe(input_layer).baseName
        if ".sde" in target_layer:
            tar_name = arcpy.Describe(target_layer).baseName.split(".")[1]
        else:
            tar_name = arcpy.Describe(target_layer).baseName
        return in_name, tar_name

    def checkSchema(self, input_layer, target_layer):
        """
        check schema of input and target dataset
        """
        skipfieldname = ['shape_length', 'shape_area', 'shape.len',
                         'shape.area', 'shape']
        arcpy.AddMessage("****** Checking Schema ******")
        input_dict = self.makeFieldDict(input_layer)
        target_dict = self.makeFieldDict(target_layer)

        tnames = self.baseName(input_layer, target_layer)

        # fields in both dataset
        combinedfield_list = (
            self.compareIntersect(input_dict.keys(), target_dict.keys()))
        arcpy.AddMessage("\n** Checking Fields List")
        # fields not in input
        missingfieldInputlist = sorted([x for x in (
            self.compareDifference(target_dict.keys(), input_dict.keys()))])
        # fields not in target
        missingfieldTargetlist = sorted([x for x in (
            self.compareDifference(input_dict.keys(), target_dict.keys()))])

        if (len(missingfieldTargetlist) + len(missingfieldInputlist)) == 0:
            arcpy.AddMessage("  - All fields are presented in input and "
                             "target")
        else:
            arcpy.AddMessage("  - Field not in input ({}):".format(tnames[0]))
            fname_list = []
            for i in missingfieldInputlist:
                if i.lower() not in skipfieldname:
                    arcpy.AddMessage("    {}".format(i.upper()))
                    fname_list.append(str(i).upper())
            arcpy.AddMessage(fname_list)
            arcpy.AddMessage(" ")

            arcpy.AddMessage("  - Field not in target ({}):".format(tnames[1]))
            fname_list = []
            for i in missingfieldTargetlist:
                if i.lower() not in skipfieldname:
                    arcpy.AddMessage("    {}".format(i.upper()))
                    fname_list.append(str(i).upper())
            arcpy.AddMessage(fname_list)
        arcpy.AddMessage("\n")

        # check field type
        arcpy.AddMessage("\n** Checking Field Type")
        fieldtypeList = [i for i in combinedfield_list if
                         input_dict[i][0] != target_dict[i][0]]
        if fieldtypeList:
            arcpy.AddMessage("  - Found type mismatch in common fields")
            for i in fieldtypeList:
                arcpy.AddMessage("    Field:{}".format(i))
                arcpy.AddMessage(
                    "    Input:{} - Len:{}, Target:{} - Len:{}".format(
                        input_dict[i][0], input_dict[i][1], target_dict[i][0],
                        target_dict[i][1]))
            arcpy.AddMessage("    Total {} field(s) type mismatch found".format(
                len(fieldtypeList)))
        else:
            arcpy.AddMessage("  - No field type mismatch in common fields")
        arcpy.AddMessage("\n")

        # check field length
        arcpy.AddMessage("\n** Checking Field Lenght")
        fieldlenList = [i for i in combinedfield_list if
                        input_dict[i][1] != target_dict[i][1]]
        if fieldlenList:
            arcpy.AddMessage("  - Found length mismatch in common fields")
            for i in fieldlenList:
                arcpy.AddMessage("    Field:{}".format(i))
                arcpy.AddMessage(
                    "    Input:{}, Target:{}".format(input_dict[i][1],
                                                   target_dict[i][1]))
            arcpy.AddMessage("    Total {} field(s) lenght mismatch "
                             "found".format(
                len(fieldlenList)))
        else:
            arcpy.AddMessage("  - No field lenght mismatch in common fields")
        arcpy.AddMessage("\n")

        # check record count
        arcpy.AddMessage("\n** Checking Record Count")
        input_row_count = int(
            arcpy.GetCount_management(input_layer).getOutput(0))
        target_row_count = int(
            arcpy.GetCount_management(target_layer).getOutput(0))
        arcpy.AddMessage('  - Total input number of records: {}'.format(
            '{0:,}'.format(input_row_count)))
        arcpy.AddMessage('  - Total target number of records: {}'.format(
            '{0:,}'.format(target_row_count)))
        arcpy.AddMessage("\n\n")

    def execute(self, parameters, messages):
        """The source code of the tool."""

        in_tables = parameters[0].valueAsText
        target_tables = parameters[1].valueAsText

        names = self.baseName(in_tables, target_tables)
        arcpy.AddMessage("****** Checking Data Name ******")
        if names[0] == names[1]:
            arcpy.AddMessage("Input and Target have same name\n\n")
        else:
            arcpy.AddMessage("Input and Target have different Name")
            arcpy.AddMessage("{} : {}\n\n".format(names[0], names[1]))

        self.checkSchema(in_tables, target_tables)

        arcpy.AddMessage("\n")
        return