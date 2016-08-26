# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Sinuosity Tool                                                 #
# Purpose:     Calculate Sinuosity Along Segments in a Stream                 #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Version:     1.3                                                            #
# Modified:    2015-Jul-29                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import sys
import arcpy
import gis_tools

# # Main Function # #
def main(fcCenterline,
         fieldName="Sinuosity",
         workspaceTemp="In_Memory"):

    arcpy.AddMessage("GNAT Sinuosity Tool")

    # Prep Inputs
    lyrCenterlineSegments = gis_tools.newGISDataset("Layer","lyrCenterlineSegments")
    ## Check to make sure field exists. If it does, clear it out. if not create new.
    fieldSinuosity = gis_tools.resetField(fcCenterline,fieldName,"DOUBLE")
    fieldSegmentLength = gis_tools.resetField(fcCenterline,"SegmentLength","DOUBLE")

    # Find Length of Segment
    arcpy.CalculateField_management(fcCenterline,fieldSegmentLength,"!shape.length!","PYTHON")

    # Find Length of Straight Line Distance
    fcSegmentEnds =  gis_tools.newGISDataset(workspaceTemp,"SegmentEnds")
    arcpy.FeatureVerticesToPoints_management(fcCenterline,fcSegmentEnds,"BOTH_ENDS")

    fcSegmentDistances = gis_tools.newGISDataset(workspaceTemp,"SegmentDistances")
    arcpy.PointsToLine_management(fcSegmentEnds,fcSegmentDistances,"ORIG_FID")

    fieldDistance = gis_tools.resetField(fcSegmentDistances,"SegmentDistance","DOUBLE")
    arcpy.CalculateField_management(fcSegmentDistances,fieldDistance,"!shape.length!","PYTHON")

    # Temporary Join of Straight Line Distance Layer
    lyrCenterlineSegments = gis_tools.newGISDataset("Layer","lyrCenterlineSegments")
    arcpy.MakeFeatureLayer_management(fcCenterline,lyrCenterlineSegments)

    arcpy.AddJoin_management(lyrCenterlineSegments,
                             arcpy.Describe(fcCenterline).OIDFieldName,
                             fcSegmentDistances,
                             "ORIG_FID")

    # Calculate Sinuosity
    ## Code Block for calculating Sinuosity
    codeblock = """def calculateSinuosity(length,distance):
        if distance == 0:
            return -9999 
        else:
            return length/distance """
    ## Calculate Field
    arcpy.CalculateField_management(lyrCenterlineSegments,
                                    fieldSinuosity,
                                    "calculateSinuosity(!" + fieldSegmentLength + "!,!SegmentDistances." + fieldDistance + "!)",
                                    "PYTHON",
                                    codeblock)

    return

# # Other Functions # #
def calculateSinuosity(dblLegnthSegment,dblLengthDistance):
    dblSinuosity = dblLegnthSegment / dblLengthDistance

    return dblSinuosity

# # Run as Script # #
if __name__ == "__main__":

    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3])