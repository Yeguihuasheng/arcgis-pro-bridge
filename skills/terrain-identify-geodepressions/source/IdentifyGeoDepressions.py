# -----------------------------------------------
# Name: Pockmark Detection: Identify Geo-Depressions
# Purpose: Semi-automated characterisation of pockmarks/Identify depressions in bathymetry grid
# ArcGIS Version: 10.3
# ArcGIS Licence Requirements: Spatial Analyst
# Python Version 2.6
# PEP8
# -----------------------------------------------

try:
    import arcpy
    import sys
    import traceback
    import math
    import os

    # Custom exceptions for spatial analysis license and bath with negative values only
    class LicenseError(Exception):
        pass

    class NotNegative(Exception):
        pass

    class NoFeatures(Exception):
        pass

    # Create RemapRange
    def remap_range_creator(raster):
        """ Creates remap ramp for reclassify tool

        Keyword arguments:
        raster -- Depression raster
        """

        minimum = arcpy.GetRasterProperties_management(raster, "MINIMUM")
        minimum = float(minimum.getOutput(0))
        remap_range = arcpy.sa.RemapRange([[minimum, -1, 1]])
        return remap_range

    # arcpy environment settings
    arcpy.env.workspace = r"in_memory"
    arcpy.env.scratchWorkspace = r"in_memory"
    arcpy.env.overwriteOutput = True

    # ArcGIS tool parameters
    raster_layer = arcpy.GetParameterAsText(0)
    z_limit = int(arcpy.GetParameterAsText(1))
    max_area = int(arcpy.GetParameterAsText(2))
    out_polygons = arcpy.GetParameterAsText(3)

    # Check if bathy is negative values only
    # Create raster object from layer (or full path data set)
    describe = arcpy.Describe(raster_layer)
    raster_source = os.path.join(describe.path, os.path.basename(raster_layer))
    bathy_dataset = arcpy.Raster(raster_source)
    maximum_value = bathy_dataset.maximum
    arcpy.AddMessage("Bathy statistics calculated.")
    if float(maximum_value) > 0:
        raise NotNegative

    # Check out Spatial Analyst extension if available
    if arcpy.CheckExtension("spatial") == "Available":
        arcpy.CheckOutExtension("spatial")
        arcpy.AddMessage("Spatial Analyst extension successfully checked out.")
    else:
        # Raise custom error
        raise LicenseError

    # Create depression polygons from bathy
    fill_raster = arcpy.sa.Fill(bathy_dataset, z_limit)
    arcpy.AddMessage("Fill raster created.")
    depression = arcpy.sa.Minus(bathy_dataset, fill_raster)
    arcpy.AddMessage("Depressions identified.")
    remap = remap_range_creator(depression)
    reclassify_raster = arcpy.sa.Reclassify(depression, "VALUE", remap, "NODATA")
    arcpy.AddMessage("Raster reclassified.")
    depression_polygons = arcpy.RasterToPolygon_conversion(reclassify_raster, None, "NO_SIMPLIFY", "VALUE")
    feature_count = arcpy.GetCount_management(depression_polygons)
    arcpy.AddMessage("{} depression polygons created.".format(feature_count))

    # Remove polygons that are too small and too big
    describe = arcpy.Describe(bathy_dataset)
    cell_size = describe.meanCellWidth
    min_area = (cell_size * 3) ** 2
    arcpy.AddField_management(depression_polygons, "AREA_M", "FLOAT")
    arcpy.CalculateField_management(depression_polygons, "AREA_M", "!SHAPE.area@SQUAREMETERS!", "PYTHON")
    sql_exp = "AREA_M >= {} AND AREA_M <= {}".format(min_area, max_area)
    depression_polygons = arcpy.MakeFeatureLayer_management(depression_polygons, None, sql_exp)
    feature_count = arcpy.GetCount_management(depression_polygons)
    arcpy.AddMessage("Polygons out of size range removed. {} polygons remaining.".format(feature_count))

    # Raise error if there are no depression polygons remaining
    if feature_count < 1:
        # Raise custom error
        raise NoFeatures

    # Find pockmark depth and convert to points ready for spatial join
    zonal_stats = arcpy.sa.ZonalStatistics(depression_polygons, "Id", depression, statistics_type="MINIMUM",
                                           ignore_nodata="DATA")
    zonal_points = arcpy.RasterToPoint_conversion(zonal_stats, None, "VALUE")

    # Field mappings for spatial join
    field_map = arcpy.FieldMap()
    field_mappings = arcpy.FieldMappings()

    field_map.addInputField(zonal_points, "GRID_CODE")
    field_map_out = field_map.outputField
    field_map_out.name = "POCK_DEP"
    field_map_out.aliasName = "POCK_DEP"
    field_map.outputField = field_map_out
    field_map.mergeRule = "MINIMUM"  # Minimum depth == deepest point

    field_mappings.addFieldMap(field_map)

    depression_polygons = arcpy.SpatialJoin_analysis(depression_polygons, zonal_points, None,
                                                     field_mapping=field_mappings)
    arcpy.AddMessage("GeoDepression depth calculated.")

    # Save output features
    arcpy.CopyFeatures_management(depression_polygons, out_polygons)

    arcpy.AddMessage("GeoDepression identification complete.")

except LicenseError:
    error = "Spatial Analyst Extension Unavailable."
    arcpy.AddError(error)
    print error

except NotNegative:
    error = "Bathy raster must be negative values only."
    arcpy.AddError(error)
    print error

except NoFeatures:
    error = "There were no depressions within the size range found."
    arcpy.AddError(error)
    print (error)

except:
    e = sys.exc_info()[1]
    arcpy.AddError(e.args[0])
    tb = sys.exc_info()[2]  # Traceback object
    tbinfo = traceback.format_tb(tb)[0]  # Traceback string
    # Concatenate error information and return to GP window
    pymsg = ('PYTHON ERRORS:\nTraceback info:\n' + tbinfo + '\nError Info: \n'
             + str(sys.exc_info()[1]))
    msgs = 'ArcPy ERRORS:\n' + arcpy.GetMessages() + '\n'
    arcpy.AddError(msgs)
    print pymsg

finally:
    # Check in spatial analysis extension
    arcpy.CheckInExtension("spatial")
    arcpy.AddMessage("Spatial analysis extension checked in.")

    # Delete in_memory
    arcpy.Delete_management('in_memory')
    arcpy.AddMessage("in_memory intermediate files deleted.")

# End of script
