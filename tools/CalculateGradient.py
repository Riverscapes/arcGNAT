# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Calculate Stream Gradient                                      #
# Purpose:     Calculates gradient (i.e. Rise/Run) per stream reach feature   #
#                                                                             #
# Author:      Jesse Langdon (jesse@southforkresearch.org)                    #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2017-July-12                                                   #
# Version:     0.1                                                            #
# Modified:                                                                   #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

import arcpy
from arcpy.sa import *

class LicenseError(Exception):
    pass

try:
    if arcpy.CheckExtension("Spatial") == "Available":
        arcpy.CheckOutExtension("Spatial")
    else:
        raise LicenseError

except LicenseError:
    print("Spatial Analyst license is unavailable.")
except arcpy.ExecuteError:
    print(arcpy.GetMessages(2))


workspace = "in_memory"


def main(in_shp, in_dem):
    """
    The main function for calculating the stream gradient per feature within a polyline
    shapefile.
    :param in_shp: input stream network polyline shapefile
    :param in_dem: input elevation raster
    :param out_shp: output stream network polyine shapefile with gradient attribute
    :return:
    """

    # Create layers for processing
    input_line = "lyr_in_shp"
    arcpy.MakeFeatureLayer_management(in_shp, input_line)

    # Plot start/end points for each stream reach feature
    pnt_start = arcpy.FeatureVerticesToPoints_management(input_line, workspace + "\\pnt_start", "START")
    pnt_end = arcpy.FeatureVerticesToPoints_management(input_line, workspace + "\\pnt_end", "END")

    # Calculate x and y coordinates for start/end points
    arcpy.AddXY_management(pnt_start)
    arcpy.AddXY_management(pnt_end)

    # Get elevation values at start/end points
    pnt_start_dem = workspace + "\\pnt_start_dem"
    pnt_end_dem = workspace + "\\pnt_end_dem"
    ExtractValuesToPoints(pnt_start, in_dem, pnt_start_dem, "INTERPOLATE", "VALUE_ONLY")
    ExtractValuesToPoints(pnt_end, in_dem, pnt_end_dem, "INTERPOLATE", "VALUE_ONLY")

    # Join elevation points to stream reach features
    arcpy.AddField_management(input_line, "ELEV_START", "DOUBLE")
    arcpy.AddJoin_management(input_line, "FID", pnt_start_dem, "ORIG_FID", "KEEP_ALL")
    arcpy.CalculateField_management(input_line, "ELEV_START", "!RASTERVALU!", "PYTHON_9.3")
    arcpy.RemoveJoin_management(input_line)
    arcpy.AddField_management(input_line, "ELEV_END", "DOUBLE")
    arcpy.AddJoin_management(input_line, "FID", pnt_end_dem, "ORIG_FID")
    arcpy.CalculateField_management(input_line, "ELEV_END", "!RASTERVALU!", "PYTHON_9.3")
    arcpy.RemoveJoin_management(input_line)

    # Add new fields to store calculations
    arcpy.AddField_management(input_line, "DIFF", "DOUBLE")
    arcpy.AddField_management(input_line, "GRADIENT", "DOUBLE")
    arcpy.AddField_management(input_line, "LENGTH_M", "DOUBLE")

    # Calculations
    arcpy.CalculateField_management(input_line, "LENGTH_M", "float(!SHAPE.LENGTH!)", "PYTHON_9.3", "#")
    arcpy.CalculateField_management(input_line, "DIFF", "!ELEV_START!-!ELEV_END!", "PYTHON_9.3", "#")
    arcpy.CalculateField_management(input_line, "GRADIENT", "!DIFF!/!LENGTH_M!", "PYTHON_9.3", "#")

    # Write to disk
    arcpy.DeleteField_management(input_line, "DIFF")
    arcpy.DeleteField_management(input_line, "LENGTH_M")
    arcpy.DeleteField_management(input_line, "ELEV_START")
    arcpy.DeleteField_management(input_line, "ELEV_END")

    return