# SCRIPT --------------------------------------------------------------------------------------------------------------
# Shared helpers for the ArcGIS Pro script tools of 'Toolbox.tbx'.
#
# Every tool script in this package follows the same pattern: read the tool parameters, call a Geometry method and show
# the result in the active map. The repeating parts of that pattern live here.
#
# Hint: This module is only meant for the toolbox scripts. The Geometry class itself never touches arcpy.env or
# arcpy.mp, so it stays usable from any script or notebook.
# ---------------------------------------------------------------------------------------------------------------------


# LICENSE -------------------------------------------------------------------------------------------------------------
# Copyright 2021 by Markus Schön
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ---------------------------------------------------------------------------------------------------------------------


# MODULES -------------------------------------------------------------------------------------------------------------
import os
from pathlib import Path

import arcpy

# ---------------------------------------------------------------------------------------------------------------------


# GENERAL INFORMATION -------------------------------------------------------------------------------------------------
__author__ = 'Markus Schön'
__copyright__ = 'Copyright 2021 by Markus Schön'
__license__ = 'Apache License, Version 2.0'

__all__ = ['PROJECT_ROOT', 'active_map', 'add_to_active_map', 'dissolve', 'output_path', 'remove_from_active_map']
# ---------------------------------------------------------------------------------------------------------------------


# ENVIRONMENTAL SETTINGS ----------------------------------------------------------------------------------------------
# The script tools always write to a user chosen output, so overwriting is the expected behaviour.
arcpy.env.overwriteOutput = True
# ---------------------------------------------------------------------------------------------------------------------


# PATHS ---------------------------------------------------------------------------------------------------------------
#: Repository root - the folder that holds 'Toolbox.tbx' and the 'data' folder.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# ---------------------------------------------------------------------------------------------------------------------


# FUNCTIONS -----------------------------------------------------------------------------------------------------------
def output_path(gdb, name):
    """
    Build the path of a tool output feature class.

    :param str gdb: Output workspace, usually a file geodatabase.
    :param str name: Output feature class name.

    :rtype: str
    :return: Full path of the output feature class.
    """

    return os.path.join(gdb, name)


def active_map():
    """
    Get the active map of the current ArcGIS Pro project.

    :rtype: arcpy.mp.Map or None
    :return: The active map, or None if the tool runs without an open project or without an active map.
    """

    try:
        project = (_ for _ in ()).throw(RuntimeError('CURRENT disabled: run in bridge mode'))
    except (OSError, RuntimeError):
        # No ArcGIS Pro project is open, e.g. when the script runs standalone
        return None

    return project.activeMap


def add_to_active_map(*paths):
    """
    Add one or more datasets to the active map.

    Data can only be added when a map is open, so this is a no-op for a project without an active map.

    :param str paths: Dataset paths. Empty values are skipped.

    :rtype: list
    :return: The added layers.
    """

    current_map = active_map()

    if current_map is None:
        return []

    return [current_map.addDataFromPath(path) for path in paths if path]


def remove_from_active_map(layer_name):
    """
    Remove every layer of a given name from the active map.

    This is needed when a tool overwrites a feature class that is currently displayed - ArcGIS Pro keeps a lock on it
    otherwise.

    :param str layer_name: Name of the layers to remove.

    :rtype: int
    :return: Number of removed layers.
    """

    current_map = active_map()

    if current_map is None or not layer_name:
        return 0

    layers = current_map.listLayers(layer_name)

    for layer in layers:
        current_map.removeLayer(layer)

    return len(layers)


def dissolve(feature, enabled):
    """
    Optionally dissolve a feature into a single feature.

    :param str feature: Input feature layer/class.
    :param enabled: Tool parameter value. Accepts the booleans of arcpy.GetParameter() as well as the 'true'/'false'
    strings of arcpy.GetParameterAsText().

    :rtype: str
    :return: The dissolved in-memory feature, or the unchanged input.
    """

    if enabled is True or str(enabled).lower() == 'true':
        dissolved = r'memory\dissolved_fc'
        arcpy.Dissolve_management(feature, dissolved)

        return dissolved

    return feature
# ---------------------------------------------------------------------------------------------------------------------
