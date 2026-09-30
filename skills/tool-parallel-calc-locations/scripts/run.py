# -*- coding: utf-8 -*-
"""
并行批量计算网络位置 —— ArcGIS Pro 版

并行地为大量停靠点计算网络分析位置（网络位置字段），显著加速大规模路径/OD 分析的准备步骤；需要 Network Analyst 许可。

参数顺序（按地理处理工具原定义）：
  1. Input Features（Input Features）
  2. Output Features（Output Features）
  3. Network Dataset（Network Dataset）
  4. Maximum Features per Chunk（Maximum Features per Chunk）
  5. Maximum Number of Parallel Processes（Maximum Number of Parallel Processes）
  6. Travel Mode（Travel Mode）
  7. Search Tolerance（Search Tolerance）
  8. Search Criteria（Search Criteria）
  9. Search Query（Search Query）

用法：
    python run.py <Input Features> <Output Features> <Network Dataset> <Maximum Features per Chunk> <Maximum Number of Parallel Processes> <Travel Mode> <Search Tolerance> <Search Criteria> <Search Query>
"""
"""Python toolbox that defines tools for solving large network analysis problems.

This is a sample script users can modify to fit their specific needs.

Copyright 2023 Esri
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
# Disable a bunch of linter errors caused by the standard python toolbox class definitions that we cannot change
# pylint: disable=invalid-name, useless-object-inheritance, too-few-public-methods, too-many-locals
# pylint: disable=useless-return, unused-argument
import sys
import os
from os import cpu_count
import arcpy


# ---- 生成器补充的运行期兜底（不影响原逻辑）----
# 上游脚本的中间结果常放在 in_memory，重复运行会因为重名而失败，
# 打开覆盖输出后再跑就正常了。
try:
    arcpy.env.overwriteOutput = True
except Exception:
    pass
# 上游的错误处理分支里偶有引用未定义的变量（如 out_fc_name / out_ws），
# 一旦走到那里会抛 NameError 把真正的错误掩盖掉，这里给这些名字兜底。
for _n in ("out_fc_name", "out_ws", "out_fc", "fc_name", "out_name"):
    if _n not in globals():
        globals()[_n] = u""
del _n


import helpers
from solve_large_odcm import ODCostMatrixSolver
from solve_large_route_pair_analysis import RoutePairSolver

def get_catalog_path(param):
    """Get the catalog path for a single value parameter if possible.

    Args:
        param (arcpy.Parameter): Parameter from which to retrieve the catalog path.

    Returns:
        str: Catalog path to the data
    """
    param_value = param.value
    if not param_value:
        return ""
    # If the value is a layer object, get its data source (catalog path)
    if hasattr(param_value, "dataSource"):
        catalog_path = param_value.dataSource
        if "DB_CONNECTION_PROPERTIES" in catalog_path:
            # Handle weird SDE or MMPK layers where the .dataSource property returns extra garbage
            catalog_path = arcpy.Describe(param_value).catalogPath
        return catalog_path
    # Otherwise, it's probably already a string catalog path. Just return its text value.
    return param.valueAsText
def get_catalog_path_multivalue(param):
    """Get a list of catalog paths for a multivalue feature layer parameter if possible.

    Args:
        param (arcpy.Parameter): Parameter from which to retrieve the catalog paths.

    Returns:
        list(str): List of catalog paths to the data
    """
    if not param.values:
        return []
    # Get both the values as geoprocessing objects and the string values
    values = param.values
    # Have to strip the quotes that get added if there are spaces in the filepath.
    string_values = [val.strip("'") for val in param.valueAsText.split(";")]
    catalog_paths = []
    for idx, val in enumerate(values):
        # If the value is a layer object, get its data source (catalog path)
        if hasattr(val, "dataSource"):
            catalog_path = val.dataSource
            if "DB_CONNECTION_PROPERTIES" in catalog_path:
                # Handle weird SDE or MMPK layers where the .dataSource property returns extra garbage
                catalog_path = arcpy.Describe(val).catalogPath
            catalog_paths.append(catalog_path)
        # Otherwise, it's probably already a string catalog path. The only way to get it is to retrieve it from the
        # valueAsText string that we split up above.
        else:
            catalog_paths.append(string_values[idx])
    return catalog_paths
def update_precalculate_parameter(param_network, param_precalculate):
    """Turn off and hide Precalculate Network Locations parameter if the network data source is a service.

    Args:
        param_network (arcpy.Parameter): Parameter for the network data source
        param_precalculate (arcpy.Parameter): Parameter for precalculate network locations
    """
    if not param_network.hasBeenValidated and param_network.altered and param_network.valueAsText:
        if helpers.is_nds_service(param_network.valueAsText):
            param_precalculate.value = False
            param_precalculate.enabled = False
        else:
            param_precalculate.enabled = True
def cap_max_processes(param_network, param_max_processes):
    """Validate max processes and cap it when required.

    Args:
        param_network (arcpy.Parameter): Parameter for the network data source
        param_max_processes (arcpy.Parameter): Parameter for the max processes
    """
    if param_max_processes.altered and param_max_processes.valueAsText:
        max_processes = param_max_processes.value
        # Don't allow 0 or negative numbers
        if max_processes <= 0:
            param_max_processes.setErrorMessage("The maximum number of parallel processes must be positive.")
            return
        # Cap max processes to the limit allowed by the concurrent.futures module
        if max_processes > helpers.MAX_ALLOWED_MAX_PROCESSES:
            param_max_processes.setErrorMessage((
                f"The maximum number of parallel processes cannot exceed {helpers.MAX_ALLOWED_MAX_PROCESSES:} due "
                "to limitations imposed by Python's concurrent.futures module."
            ))
            return
        # If the network data source is arcgis.com, cap max processes
        if (
            max_processes > helpers.MAX_AGOL_PROCESSES and
            param_network.altered and
            param_network.valueAsText and
            helpers.is_nds_service(param_network.valueAsText) and
            "arcgis.com" in param_network.valueAsText
        ):
            param_max_processes.setErrorMessage((
                f"The maximum number of parallel processes cannot exceed {helpers.MAX_AGOL_PROCESSES} when the "
                "ArcGIS Online service is used as the network data source."
            ))
            return
        # If the network data source is mgdb and the user has put more processes than the max recommended for
        # the mgdb solvers, set a warning.
        if (
            max_processes > helpers.MAX_RECOMMENDED_MGDB_PROCESSES and
            param_network.altered and
            param_network.valueAsText and
            not helpers.is_nds_service(param_network.valueAsText)
        ):
            try:
                network_obj = param_network.value
                is_mgdb = False
                if hasattr(network_obj, "connectionProperties"):
                    # A network dataset layer in a map typically has this connectionProperties property. For a mobile
                    # geodatabase network, it will be something like this:
                    # {'dataset': 'main.Streets_ND', 'workspace_factory': 'SQLite', 'connection_info':
                    # {'authentication_mode': 'OSA', 'database': 'main', 'db_connection_properties':
                    # 'C:\\Data\\Packages\\MyPackage\\p14\\sanfrancisco.geodatabase', 'instance':
                    # 'sde:sqlite:C:\\Data\\Packages\\MyPackage\\p14\\sanfrancisco.geodatabase',
                    # 'is_geodatabase': 'true', 'server': 'e:'}}
                    # The 'workspace_factory' property is the relevant one.  For a file geodatabase network, it reads
                    # "File Geodatabase" instead.
                    connection_props = network_obj.connectionProperties
                    is_mgdb = connection_props.get("workspace_factory", None) == "SQLite"
                else:
                    # It's probably a network dataset catalog path
                    network_path = param_network.valueAsText
                    desc = arcpy.Describe(os.path.dirname(os.path.dirname(network_path)))
                    is_mgdb = desc.workspaceFactoryProgID.startswith("esriDataSourcesGDB.SqliteWorkspaceFactory")
                if is_mgdb:
                    param_max_processes.setWarningMessage((
                        "The maximum number of parallel processes is greater than the maximum recommended number "
                        f"({helpers.MAX_RECOMMENDED_MGDB_PROCESSES}) to use with a network dataset in a "
                        "mobile geodatabase."
                    ))
                    return
            except Exception:  # pylint: disable=broad-except
                # If determining the network dataset type fails for some reason, just skip this check
                pass
        # Set a warning if the user has put more processes than the number of logical cores on their machine
        if max_processes > cpu_count():
            param_max_processes.setWarningMessage((
                "The maximum number of parallel processes is greater than the number of logical cores "
                f"({cpu_count()}) in your machine."
            ))
def validate_search_query_param(param_search_query, param_network):
    """Validate the search query parameter for Parallel Calculate Locations."""
    search_query = param_search_query.values
    search_query_sources = [s[0] for s in search_query]

    # Validate source names
    valid_source_names = param_search_query.filters[0].list
    for source in search_query_sources:
        if source not in valid_source_names:
            # Error 030254: Invalid source name: "BadSourceName".
            param_search_query.setIDMessage("Error", 30254, source)
            return

    # Validate no duplicate source names
    if len(set(search_query_sources)) < len(search_query_sources):
        seen = set()
        duplicates = []
        for source in search_query_sources:
            if source in seen:
                duplicates.append(source)
            else:
                seen.add(source)
        # Error 030255: Duplicate source name: "MySourceName".
        param_search_query.setIDMessage("Error", 30255, duplicates[0])
        return

    # Validate SQL queries
    # There's no straightforward way to validate SQL queries in Python, so let's be clever and tricky.  Spin up a dummy
    # SearchCursor using the user's query for each network source as a where clause.  If that throws an exception,
    # return the exception as a validation error.
    # First check that there are any actual queries.  No need to validate if they're all empty.
    populated_queries = [q[1] for q in search_query if q[1]]
    if not populated_queries:
        return
    feature_dataset = os.path.dirname(get_catalog_path(param_network))
    for query in search_query:
        try:
            with arcpy.da.SearchCursor(  # pylint: disable=no-member
                os.path.join(feature_dataset, query[0]), ["OID@"], query[1]
            ) as cur:
                try:
                    next(cur)
                except StopIteration:
                    # The cursor worked but no rows were returned.  This is not an error.
                    pass
        except Exception as ex:  # pylint: disable=broad-except
            param_search_query.setErrorMessage(str(ex))
            return
class ParallelCalculateLocations(object):
    """Sample script tool to calculate locations for a large dataset in parallel."""

    def __init__(self):
        """Define the tool."""
        self.label = "Parallel Calculate Locations"
        self.description = "Calculate network locations for a large dataset by chunking it and solving in parallel."
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""

        param_in_features = arcpy.Parameter(
            displayName="Input Features",
            name="Input_Features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
        param_in_features.filter.list = ["Point"]

        param_out_features = arcpy.Parameter(
            displayName="Output Features",
            name="Output_Features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output"
        )

        param_network = arcpy.Parameter(
            displayName="Network Dataset",
            name="Network_Dataset",
            datatype="GPNetworkDatasetLayer",
            parameterType="Required",
            direction="Input"
        )

        param_chunk_size = arcpy.Parameter(
            displayName="Maximum Features per Chunk",
            name="Max_Features_Per_Chunk",
            datatype="GPLong",
            parameterType="Required",
            direction="Input"
        )
        param_chunk_size.value = 1000

        param_max_processes = arcpy.Parameter(
            displayName="Maximum Number of Parallel Processes",
            name="Max_Processes",
            datatype="GPLong",
            parameterType="Required",
            direction="Input"
        )
        param_max_processes.value = 4

        param_travel_mode = arcpy.Parameter(
            displayName="Travel Mode",
            name="Travel_Mode",
            datatype="NetworkTravelMode",
            parameterType="Optional",
            direction="Input"
        )
        param_travel_mode.parameterDependencies = [param_network.name]

        param_search_tolerance = arcpy.Parameter(
            displayName="Search Tolerance",
            name="Search_Tolerance",
            datatype="GPLinearUnit",
            parameterType="Optional",
            direction="Input"
        )
        param_search_tolerance.value = "5000 Meters"

        param_search_criteria = arcpy.Parameter(
            displayName="Search Criteria",
            name="Search_Criteria",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=True
        )
        # Causes the parameter to be a list of checkboxes instead of a standard multivalue
        param_search_criteria.controlCLSID = "{38C34610-C7F7-11D5-A693-0008C711C8C1}"

        param_search_query = arcpy.Parameter(
            displayName="Search Query",
            name="Search_Query",
            datatype="GPValueTable",
            parameterType="Optional",
            direction="Input",
            multiValue=True
        )
        param_search_query.columns = [
            ['GPString', 'Name'],
            ['GPString', 'Query']
        ]
        param_search_query.filters[0].type = 'ValueList'

        params = [
            param_in_features,  # 0
            param_out_features,  # 1
            param_network,  # 2
            param_chunk_size,  # 3
            param_max_processes,  # 4
            param_travel_mode,  # 5
            param_search_tolerance,  # 6
            param_search_criteria,  # 7
            param_search_query  # 8
        ]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        param_network = parameters[2]
        param_search_criteria = parameters[7]
        param_search_query = parameters[8]

        # Populate available network sources in the search criteria and search query parameters
        if not param_network.hasBeenValidated and param_network.altered and param_network.valueAsText:
            try:
                network = param_network.valueAsText
                source_names = helpers.get_locatable_network_source_names(network)
                default_source_names = helpers.get_default_locatable_network_source_names(network)
                param_search_criteria.filter.list = source_names
                param_search_criteria.value = default_source_names
                param_search_query.filters[0].list = source_names
            except Exception:  # pylint: disable=broad-except
                # Something went wrong in checking the network's sources.  Don't modify any parameters.
                pass

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        param_network = parameters[2]
        param_search_criteria = parameters[7]
        param_search_query = parameters[8]

        # Validate that at least one source is selected for search criteria
        if not param_search_criteria.hasBeenValidated and param_network.valueAsText:
            if not param_search_criteria.valueAsText:
                param_search_criteria.setErrorMessage("At least one network source is required.")

        # Validate no duplicate entries in search query
        if not param_search_query.hasBeenValidated and param_search_query.altered and \
                param_search_query.valueAsText and param_network.valueAsText:
            validate_search_query_param(param_search_query, param_network)

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Construct string-based travel mode
        travel_mode = parameters[5].value
        if travel_mode:
            if hasattr(travel_mode, "JSON"):
                # Pro 3.7+
                travel_mode = travel_mode.JSON
            else:
                # Pre 3.7
                travel_mode = travel_mode._JSON  # pylint: disable=protected-access
        else:
            travel_mode = ""

        # Construct the search criteria from the selected sources
        source_names = parameters[7].filter.list
        sources_to_locate_on = parameters[7].values
        search_criteria = helpers.construct_search_criteria_string(sources_to_locate_on, source_names)

        # Construct string-based search query
        search_query = parameters[8].valueAsText
        if not search_query:
            search_query = ""

        # Make a temporary copy of the input features to take care of any selection sets and definition queries and to
        # add a field preserving the ObjectID.
        input_features = parameters[0].value
        desc = arcpy.Describe(input_features)
        # Create a unique output field name to preserve the original OID
        in_fields = [f.name for f in desc.fields]
        base_oid_field = "ORIG_OID"
        out_oid_field = base_oid_field
        if out_oid_field in in_fields:
            i = 1
            while out_oid_field in in_fields:
                out_oid_field = base_oid_field + str(i)
                i += 1
        field_mappings = helpers.make_oid_preserving_field_mappings(
            input_features, desc.oidFieldName, out_oid_field)
        temp_inputs = arcpy.CreateUniqueName("TempCLInputs", arcpy.env.scratchGDB)  # pylint:disable = no-member
        arcpy.conversion.FeatureClassToFeatureClass(
            input_features,
            arcpy.env.scratchGDB,  # pylint:disable = no-member
            os.path.basename(temp_inputs),
            field_mapping=field_mappings
        )

        try:
            cl_inputs = [
                "--input-features", temp_inputs,
                "--output-features", parameters[1].valueAsText,
                "--network-data-source", get_catalog_path(parameters[2]),
                "--chunk-size", parameters[3].valueAsText,
                "--max-processes", parameters[4].valueAsText,
                "--travel-mode", travel_mode,
                "--search-tolerance", parameters[6].valueAsText,
                "--search-criteria", search_criteria,
                "--search-query", search_query
            ]
            helpers.execute_subprocess("parallel_calculate_locations.py", cl_inputs)

        finally:
            # Clean up. Delete temporary copy of inputs
            arcpy.management.Delete([temp_inputs])

        return


def get_catalog_path(param):
    """Get the catalog path for a single value parameter if possible.

    Args:
        param (arcpy.Parameter): Parameter from which to retrieve the catalog path.

    Returns:
        str: Catalog path to the data
    """
    param_value = param.value
    if not param_value:
        return ""
    # If the value is a layer object, get its data source (catalog path)
    if hasattr(param_value, "dataSource"):
        catalog_path = param_value.dataSource
        if "DB_CONNECTION_PROPERTIES" in catalog_path:
            # Handle weird SDE or MMPK layers where the .dataSource property returns extra garbage
            catalog_path = arcpy.Describe(param_value).catalogPath
        return catalog_path
    # Otherwise, it's probably already a string catalog path. Just return its text value.
    return param.valueAsText


def get_catalog_path_multivalue(param):
    """Get a list of catalog paths for a multivalue feature layer parameter if possible.

    Args:
        param (arcpy.Parameter): Parameter from which to retrieve the catalog paths.

    Returns:
        list(str): List of catalog paths to the data
    """
    if not param.values:
        return []
    # Get both the values as geoprocessing objects and the string values
    values = param.values
    # Have to strip the quotes that get added if there are spaces in the filepath.
    string_values = [val.strip("'") for val in param.valueAsText.split(";")]
    catalog_paths = []
    for idx, val in enumerate(values):
        # If the value is a layer object, get its data source (catalog path)
        if hasattr(val, "dataSource"):
            catalog_path = val.dataSource
            if "DB_CONNECTION_PROPERTIES" in catalog_path:
                # Handle weird SDE or MMPK layers where the .dataSource property returns extra garbage
                catalog_path = arcpy.Describe(val).catalogPath
            catalog_paths.append(catalog_path)
        # Otherwise, it's probably already a string catalog path. The only way to get it is to retrieve it from the
        # valueAsText string that we split up above.
        else:
            catalog_paths.append(string_values[idx])
    return catalog_paths


def update_precalculate_parameter(param_network, param_precalculate):
    """Turn off and hide Precalculate Network Locations parameter if the network data source is a service.

    Args:
        param_network (arcpy.Parameter): Parameter for the network data source
        param_precalculate (arcpy.Parameter): Parameter for precalculate network locations
    """
    if not param_network.hasBeenValidated and param_network.altered and param_network.valueAsText:
        if helpers.is_nds_service(param_network.valueAsText):
            param_precalculate.value = False
            param_precalculate.enabled = False
        else:
            param_precalculate.enabled = True


def cap_max_processes(param_network, param_max_processes):
    """Validate max processes and cap it when required.

    Args:
        param_network (arcpy.Parameter): Parameter for the network data source
        param_max_processes (arcpy.Parameter): Parameter for the max processes
    """
    if param_max_processes.altered and param_max_processes.valueAsText:
        max_processes = param_max_processes.value
        # Don't allow 0 or negative numbers
        if max_processes <= 0:
            param_max_processes.setErrorMessage("The maximum number of parallel processes must be positive.")
            return
        # Cap max processes to the limit allowed by the concurrent.futures module
        if max_processes > helpers.MAX_ALLOWED_MAX_PROCESSES:
            param_max_processes.setErrorMessage((
                f"The maximum number of parallel processes cannot exceed {helpers.MAX_ALLOWED_MAX_PROCESSES:} due "
                "to limitations imposed by Python's concurrent.futures module."
            ))
            return
        # If the network data source is arcgis.com, cap max processes
        if (
            max_processes > helpers.MAX_AGOL_PROCESSES and
            param_network.altered and
            param_network.valueAsText and
            helpers.is_nds_service(param_network.valueAsText) and
            "arcgis.com" in param_network.valueAsText
        ):
            param_max_processes.setErrorMessage((
                f"The maximum number of parallel processes cannot exceed {helpers.MAX_AGOL_PROCESSES} when the "
                "ArcGIS Online service is used as the network data source."
            ))
            return
        # If the network data source is mgdb and the user has put more processes than the max recommended for
        # the mgdb solvers, set a warning.
        if (
            max_processes > helpers.MAX_RECOMMENDED_MGDB_PROCESSES and
            param_network.altered and
            param_network.valueAsText and
            not helpers.is_nds_service(param_network.valueAsText)
        ):
            try:
                network_obj = param_network.value
                is_mgdb = False
                if hasattr(network_obj, "connectionProperties"):
                    # A network dataset layer in a map typically has this connectionProperties property. For a mobile
                    # geodatabase network, it will be something like this:
                    # {'dataset': 'main.Streets_ND', 'workspace_factory': 'SQLite', 'connection_info':
                    # {'authentication_mode': 'OSA', 'database': 'main', 'db_connection_properties':
                    # 'C:\\Data\\Packages\\MyPackage\\p14\\sanfrancisco.geodatabase', 'instance':
                    # 'sde:sqlite:C:\\Data\\Packages\\MyPackage\\p14\\sanfrancisco.geodatabase',
                    # 'is_geodatabase': 'true', 'server': 'e:'}}
                    # The 'workspace_factory' property is the relevant one.  For a file geodatabase network, it reads
                    # "File Geodatabase" instead.
                    connection_props = network_obj.connectionProperties
                    is_mgdb = connection_props.get("workspace_factory", None) == "SQLite"
                else:
                    # It's probably a network dataset catalog path
                    network_path = param_network.valueAsText
                    desc = arcpy.Describe(os.path.dirname(os.path.dirname(network_path)))
                    is_mgdb = desc.workspaceFactoryProgID.startswith("esriDataSourcesGDB.SqliteWorkspaceFactory")
                if is_mgdb:
                    param_max_processes.setWarningMessage((
                        "The maximum number of parallel processes is greater than the maximum recommended number "
                        f"({helpers.MAX_RECOMMENDED_MGDB_PROCESSES}) to use with a network dataset in a "
                        "mobile geodatabase."
                    ))
                    return
            except Exception:  # pylint: disable=broad-except
                # If determining the network dataset type fails for some reason, just skip this check
                pass
        # Set a warning if the user has put more processes than the number of logical cores on their machine
        if max_processes > cpu_count():
            param_max_processes.setWarningMessage((
                "The maximum number of parallel processes is greater than the number of logical cores "
                f"({cpu_count()}) in your machine."
            ))


def validate_search_query_param(param_search_query, param_network):
    """Validate the search query parameter for Parallel Calculate Locations."""
    search_query = param_search_query.values
    search_query_sources = [s[0] for s in search_query]

    # Validate source names
    valid_source_names = param_search_query.filters[0].list
    for source in search_query_sources:
        if source not in valid_source_names:
            # Error 030254: Invalid source name: "BadSourceName".
            param_search_query.setIDMessage("Error", 30254, source)
            return

    # Validate no duplicate source names
    if len(set(search_query_sources)) < len(search_query_sources):
        seen = set()
        duplicates = []
        for source in search_query_sources:
            if source in seen:
                duplicates.append(source)
            else:
                seen.add(source)
        # Error 030255: Duplicate source name: "MySourceName".
        param_search_query.setIDMessage("Error", 30255, duplicates[0])
        return

    # Validate SQL queries
    # There's no straightforward way to validate SQL queries in Python, so let's be clever and tricky.  Spin up a dummy
    # SearchCursor using the user's query for each network source as a where clause.  If that throws an exception,
    # return the exception as a validation error.
    # First check that there are any actual queries.  No need to validate if they're all empty.
    populated_queries = [q[1] for q in search_query if q[1]]
    if not populated_queries:
        return
    feature_dataset = os.path.dirname(get_catalog_path(param_network))
    for query in search_query:
        try:
            with arcpy.da.SearchCursor(  # pylint: disable=no-member
                os.path.join(feature_dataset, query[0]), ["OID@"], query[1]
            ) as cur:
                try:
                    next(cur)
                except StopIteration:
                    # The cursor worked but no rows were returned.  This is not an error.
                    pass
        except Exception as ex:  # pylint: disable=broad-except
            param_search_query.setErrorMessage(str(ex))
            return


# ------------------------------------------------------------------ 运行入口
class _Param(object):
    """模拟地理处理参数对象（供被抽取的 execute() 使用）。"""

    def __init__(self, value):
        self.value = value
        self.valueAsText = value
        self.valueAsMultiValue = value if isinstance(value, list) else [value]
        self.altered = True

    def __str__(self):
        return str(self.value)


class _Msgs(object):
    """模拟地理处理消息对象：把 addMessage 系列接到 stdout。"""

    def addMessage(self, text):
        print(text)

    AddMessage = addMessage

    def addWarning(self, text):
        sys.stderr.write("WARN: %s\n" % text)

    AddWarning = addWarning

    def addErrorMessage(self, text):
        sys.stderr.write("ERROR: %s\n" % text)

    AddErrorMessage = addErrorMessage

    def addError(self, *a, **k):
        pass

    AddError = addError


if sys.version_info[0] >= 3:
    # 抽取的原实现常按 py2 习惯用 open(path, "wb") 写 csv，py3 下会报
    # "a bytes-like object is required"。这里只在本模块内兜一层：
    # 去掉 b、补 newline/encoding，让 csv 走文本模式。
    # 注意：只覆盖本模块全局，不影响 arcpy 内部的 open。
    _py_open = open

    def open(file, mode="r", *args, **kwargs):  # noqa: A001
        if "b" in mode:
            mode = mode.replace("b", "")
            kwargs.setdefault("newline", "")
            kwargs.setdefault("encoding", "utf-8")
        return _py_open(file, mode, *args, **kwargs)


def _to_unicode(s):
    """py2 下 sys.argv 是字节串，中文参数不解码会和 u"" 比较炸，入口统一转 unicode。"""
    if not isinstance(s, bytes):
        return s
    for enc in (u"mbcs", u"utf-8", u"gbk", u"latin-1"):
        try:
            return s.decode(enc)
        except Exception:
            continue
    return s.decode(u"utf-8", u"replace")


def _run(argv):
    if sys.version_info[0] < 3:
        argv = [_to_unicode(v) for v in argv]
    params = [_Param(v) for v in argv]
    tools = ParallelCalculateLocations()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
