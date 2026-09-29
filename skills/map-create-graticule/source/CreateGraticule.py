# -----------------------------------------------
# Name: Create Graticule
# Purpose: Creates graticule of desired interval ranging from 1 second to 30 degrees
# ArcGIS Version: 10.3
# Python Version 2.6
# PEP8
# -----------------------------------------------

try:
    import arcpy
    import sys
    import traceback

    def dms_to_dd(deg, mins, secs):
        """Convert degrees, minutes and seconds into decimal degrees

        Keyword arguments:
        deg     -- Degrees
        mins    -- minutes
        secs    -- seconds
        """
        return deg + (mins / 60.0) + (secs / 3600.0)

    # arcpy environment settings
    arcpy.env.workspace = r'in_memory'
    arcpy.env.scratchWorkspace = r'in_memory'
    arcpy.env.overwriteOutput = True

    # ArcGIS tool parameters
    degrees = int(arcpy.GetParameterAsText(0))  # degrees
    minutes = int(arcpy.GetParameterAsText(1))  # minutes
    seconds = int(arcpy.GetParameterAsText(2))  # seconds
    out_feature_class = arcpy.GetParameterAsText(3)  # Output feature class

    # Variables prepared for GP
    mxd = arcpy.mapping.MapDocument("CURRENT")
    data_frame = mxd.activeDataFrame
    sr = data_frame.spatialReference
    arcpy.env.outputCoordinateSystem = sr
    extent = data_frame.extent
    lower_left = extent.lowerLeft
    upper_right = extent.upperRight
    interval_param = dms_to_dd(degrees, minutes, seconds)
    arcpy.AddMessage("Extent calculated.")

    # Construct coordinate variables for Fishnet. Round so that they fall on a line of lat and long.
    origin_coord = str(round(lower_left.X)) + ' ' + str(round(lower_left.Y))
    corner_coord = str(round(upper_right.X)) + ' ' + str(round(upper_right.Y))
    orient_coord = str(round(lower_left.X)) + ' ' + str(round(lower_left.Y + 10))  # Add 10 to Y for orientation
    fishnet = arcpy.CreateFishnet_management("fishnet", origin_coord, orient_coord, interval_param, interval_param,
                                             corner_coord=corner_coord, geometry_type="POLYLINE")
    arcpy.AddMessage("Fishnet created.")

    # Create fields and perform field calculation
    arcpy.AddField_management(fishnet, "LINE", "TEXT", field_length=20)
    arcpy.AddField_management(fishnet, "DMS", "TEXT", field_length=50)

    line_codeblock = """def line_orientation(line):
        firstX = line.firstPoint.X
        firstY = line.firstPoint.Y
        lastX = line.lastPoint.X
        lastY = line.lastPoint.Y
        if abs(firstX - lastX) < abs(firstY - lastY):
            return "Longitude"
        else:
            return "Latitude"
            """

    dms_codeblock = ("""def dd_to_dms (orientation, shape):
        if orientation == "Latitude":
            dd = round(shape.firstPoint.Y, 3)
        elif orientation ==  "Longitude":
            dd = round(shape.firstPoint.X, 3)
        degrees = int(dd)
        minutes = int(60 * (dd - degrees))
        seconds = 60 * (60 * (dd - degrees) - minutes)
        
        if orientation == "Longitude":
            if degrees < 0:
                direction = "W"
            elif degrees > 0:
                direction = "E"
            else:
                direction = ""
        elif orientation == "Latitude":
            if degrees < 0:
                direction = "S"
            elif degrees > 0:
                direction = "N"
            else:
                direction = ""          
        notation = str(abs(degrees)) + ":" + str(abs(minutes))"""
        """+ ":" + str(abs(seconds)) + " " + direction
        return notation
        """)

    arcpy.CalculateField_management(fishnet, "LINE", "line_orientation (!Shape!)",
                                    "PYTHON_9.3", line_codeblock)
    arcpy.CalculateField_management(fishnet, "DMS", "dd_to_dms (!LINE!, !Shape!)",
                                    "PYTHON_9.3", dms_codeblock)
    arcpy.AddMessage("Fields calculated.")

    # Densify so there are enough intermediate vertices so graticule lines 'curve' when projected.
    densify_distance = interval_param/3.00
    arcpy.Densify_edit(fishnet, 'DISTANCE', densify_distance)
    arcpy.AddMessage("Densify complete.")

    # Create output feature class    
    arcpy.CopyFeatures_management(fishnet, out_feature_class)

except:
    tb = sys.exc_info()[2]  # Traceback object
    tbinfo = traceback.format_tb(tb)[0]  # Traceback string
    # Concatenate error information and return to GP window
    pymsg = ('PYTHON ERRORS:\nTraceback info:\n' + tbinfo + '\nError Info: \n'
            + str(sys.exc_info()[1]))
    msgs = 'ArcPy ERRORS:\n' + arcpy.GetMessage(2) + '\n'
    arcpy.AddError(msgs)
    print pymsg

finally:
    # Delete in_memory
    arcpy.Delete_management('in_memory')

# End of script
