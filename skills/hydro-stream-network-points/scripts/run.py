# -*- coding: utf-8 -*-
"""
河网转点并统计排水面积 —— ArcGIS Pro 版

把河网线要素转为节点点，并给每个点挂上排水面积、高程与路由属性，用于按排水面积把河网切分成相对均质的河段。

参数顺序（按工具原定义）：
  1. feature_dataset（feature_dataset）
  2. stream_network（stream_network）
  3. flow_accum（flow_accum）
  4. dem（dem）

用法：
    python run.py <feature_dataset> <stream_network> <flow_accum> <dem>
"""

import os
import sys

import arcpy


def _argv(i):
    """替代 arcpy.GetParameterAsText(i)：从命令行取第 i 个参数（字符串）。"""
    if len(sys.argv) > i + 1:
        return sys.argv[i + 1]
    return u""


def _gp(i):
    """替代 arcpy.GetParameter(i)：按常见类型还原命令行参数（数值/布尔/字符串）。"""
    if len(sys.argv) <= i + 1:
        return None
    v = sys.argv[i + 1]
    if v == u"":
        return None
    low = v.lower()
    if low == u"true":
        return True
    if low == u"false":
        return False
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


"""____________________________________________________________________________
Script Name:          _04a_StreamNetworkPoints.py
Description:          Converts a stream network to points and calculates the
                      drainage area.
Date:                 5/26/2018

Usage:
The output of this tool is used to help divide a stream network into
relatively homogeneous segments based on drainage area.

Drainage area will be in the units of the flow accumulation model.

Parameters:
feature_dataset       -- Path to the feature dataset
stream_network        -- Path to the edited stream network feature class
flow_accum            -- Path to the flow accumulation model
dem                   -- Path to the digital elevation model (DEM)

Outputs:
stream_network_points -- a new point feature class of synthetic stream
                         network points with route, drainage area, and
                         elevation attributes
____________________________________________________________________________"""

import os
import arcpy
from arcpy.sa import *

def StreamNetworkPoints(feature_dataset, stream_network, flow_accum, dem):
    arcpy.CheckOutExtension("Spatial")

    # Set environment variables
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = os.path.dirname(feature_dataset)

    # Get spatial reference of FAC
    spatial_ref = arcpy.Describe(flow_accum).spatialReference

    # List parameter values
    arcpy.AddMessage("Workspace: {}".format(arcpy.env.workspace))
    arcpy.AddMessage("Stream Network: "
                     "{}".format(arcpy.Describe(stream_network).baseName))
    arcpy.AddMessage("Flow Accumulation Model: "
                     "{}".format(arcpy.Describe(flow_accum).baseName))
    arcpy.AddMessage("Digital Elevation Model: "
                     "{}".format(arcpy.Describe(dem).baseName))

    ## Convert stream_network fc to a route
    # Add a field to hold the linear referencing route `from_measure`
    # Check if the field already exists and if not add it
    field_names = [f.name for f in arcpy.ListFields(stream_network)]
    if "from_measure" not in field_names:
        arcpy.AddField_management(in_table = stream_network,
                                  field_name = "from_measure",
                                  field_type = "DOUBLE")

    # Set the value of the cross section `from_measure` to zero in units meters
    arcpy.CalculateField_management(in_table = stream_network,
                                    field = "from_measure",
                                    expression = "!shape.length@kilometers!",
                                    expression_type = "PYTHON_9.3")

    # Add a field to hold the linear referencing route `to_measure`
    if "to_measure" not in field_names:
        arcpy.AddField_management(in_table = stream_network,
                                  field_name = "to_measure",
                                  field_type = "DOUBLE")

    # Set the value of the cross section `to_measure` to the length of the
    # stream_network in units kilometers
    arcpy.CalculateField_management(in_table = stream_network,
                                    field = "to_measure",
                                    expression = "0",
                                    expression_type = "PYTHON_9.3")

    # Convert stream_network fc into a route
    stream_network_route = os.path.join(feature_dataset, "stream_network_route")
    arcpy.CreateRoutes_lr(in_line_features = stream_network,
                          route_id_field = "ReachName",
                          out_feature_class = stream_network_route,
                          measure_source = "TWO_FIELDS",
                          from_measure_field = "from_measure",
                          to_measure_field = "to_measure")
    arcpy.AddMessage("Stream network route created")

    # Convert stream network feature vertices to points
    stream_network_points = os.path.join(feature_dataset, "stream_network_points")
    arcpy.FeatureVerticesToPoints_management(in_features = stream_network_route,
                                    out_feature_class = stream_network_points)
    arcpy.AddMessage("Converted the stream network to points")

    # Add x, y, z, and m values to the `cross_section_points` feature class
    arcpy.AddGeometryAttributes_management(
                                    Input_Features = stream_network_points,
                                    Geometry_Properties = "POINT_X_Y_Z_M",
                                    Length_Unit = "KILOMETERS")

    # Set the first m-value for each stream network to zero. The `create route`
    # tool sets it to NULL.
    arcpy.CalculateField_management(in_table = stream_network_points,
                                    field = "POINT_M",
                                    expression = "setNull2Zero(!POINT_M!)",
                                    code_block = """def setNull2Zero(m):
                                                        if m is None:
                                                            return 0
                                                        else:
                                                            return m""",
                                    expression_type = "PYTHON_9.3")

    # Delete un-needed fields
    arcpy.DeleteField_management(in_table = stream_network_points,
                                 drop_field = ["ORIG_FID","POINT_Z"])
    arcpy.AddMessage("Added stream network route lengths")

    # Add flow accumulation values to the stream_network_points fc
    arcpy.sa.ExtractMultiValuesToPoints(
                                  in_point_features = stream_network_points,
                                  in_rasters = [flow_accum],
                                  bilinear_interpolate_values = "NONE")
    # Add a field to to the stream_network_points fc to hold watershed area
    # Check if the field already exists and if not add it
    field_names = [f.name for f in arcpy.ListFields(stream_network_points)]
    if "Watershed_Area_SqMile" not in field_names:
        arcpy.AddField_management(in_table = stream_network_points,
                                  field_name = "Watershed_Area_SqMile",
                                  field_type = "DOUBLE")
    # Convert flow accumulation cell counts to area in square miles
    cell_size = str(arcpy.GetRasterProperties_management(flow_accum,
                                                         "CELLSIZEX"))
    # Expression to convert sq m to sq mi: 1 sq m = 0.0000003861 sq mile
    meters_sqmi = ("((float({0}) * float({0})) * 0.0000003861) * "
                  "!{1}!".format(cell_size, arcpy.Describe(flow_accum).baseName))

    if spatial_ref.linearUnitName == "Meter":
        arcpy.CalculateField_management(in_table = stream_network_points,
                                        field = "Watershed_Area_SqMile",
                                        expression = meters_sqmi,
                                        expression_type = "PYTHON_9.3")
    else:
        # Error
        arcpy.AddError("    Watershed linear unit not recognized."
                       " Area not calculated")
    # Delete un-needed fields
    arcpy.DeleteField_management(in_table = stream_network_points,
                                 drop_field = [arcpy.Describe(flow_accum).baseName])
    arcpy.AddMessage("Added stream network drainage area")

    # Add elevation values to the stream_network_points fc
    arcpy.sa.ExtractMultiValuesToPoints(
                      in_point_features = stream_network_points,
                      in_rasters = [dem],
                      bilinear_interpolate_values = "NONE")
    arcpy.AlterField_management(in_table = stream_network_points,
                                field = arcpy.Describe(dem).baseName,
                                new_field_name = "Z",
                                new_field_alias = "Z")
    arcpy.AddMessage("Added stream network elevations")

    # Return
    arcpy.SetParameter(4, stream_network_points)

    # Cleanup
    arcpy.Delete_management(in_data = stream_network_route)


def main():
    # Call the StreamNetworkPoints function with command line parameters
    StreamNetworkPoints(feature_dataset, stream_network, flow_accum, dem)

if __name__ == "__main__":
    # Get input parameters
    feature_dataset  = _argv(0)
    stream_network   = _argv(1)
    flow_accum       = _argv(2)
    dem              = _argv(3)

    main()
