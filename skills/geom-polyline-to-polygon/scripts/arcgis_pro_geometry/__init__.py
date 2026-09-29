# SCRIPT --------------------------------------------------------------------------------------------------------------
# Public API of the arcgis_pro_geometry package.
#
# Usage:
#     from arcgis_pro_geometry import Geometry
#
#     with Geometry(feature_layer) as geom:
#         geom.boundary(output_path)
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
from .geometry import Geometry, GeometryError

# ---------------------------------------------------------------------------------------------------------------------


# GENERAL INFORMATION -------------------------------------------------------------------------------------------------
__author__ = 'Markus Schön'
__copyright__ = 'Copyright 2021 by Markus Schön'
__license__ = 'Apache License, Version 2.0'
__version__ = '2.0.0'

__all__ = ['Geometry', 'GeometryError', '__version__']
# ---------------------------------------------------------------------------------------------------------------------
