# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Transfer Attributes Tool                                       #
# Purpose:     Transfer attributes from one line layer to another             #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              Jesse Langdon (jesse@southforkresearch.org)                    #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-01-08                                                     #
# Modified:    2017-05-03                                                     #
#                                                                             #
# Copyright:   (c) Kelly Whitehead, Jesse Langdon                             #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python


# Import modules
import arcpy
import gis_tools
import DividePolygonBySegment


def main(fcFromLine,
         fcToLine,
         fcOutputLineNetwork,
         tempWorkspace=''):

    gis_tools.resetData(fcOutputLineNetwork)

    fcFromLineTemp = gis_tools.newGISDataset(tempWorkspace, "GNAT_TLA_FromLineTemp")
    arcpy.MakeFeatureLayer_management(fcFromLine, "lyrFromLine")
    arcpy.CopyFeatures_management("lyrFromLine", fcFromLineTemp)

    # Make bounding polygon for "From" line feature class
    arcpy.AddMessage("GNAT TLA: Create buffer polygon around 'From' network")
    fcFromLineBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_FromLineBuffer")
    arcpy.Buffer_analysis(fcFromLineTemp,fcFromLineBuffer,"10 Meters","FULL","ROUND","ALL")

    # Select features from "To" line feature class that are inside "From" line buffer
    lyrFromLineBuffer = gis_tools.newGISDataset("Layer", "lyrFromLineBuffer")
    arcpy.MakeFeatureLayer_management(fcFromLineBuffer, lyrFromLineBuffer)
    lyrToLine = gis_tools.newGISDataset("Layer", "lyrToLine")
    arcpy.MakeFeatureLayer_management(fcToLine, lyrToLine)
    arcpy.SelectLayerByLocation_management(lyrToLine, "WITHIN", lyrFromLineBuffer, "#", "NEW_SELECTION")
    fcToLineWithinFromBuffer = arcpy.FeatureClassToFeatureClass_conversion(lyrToLine, tempWorkspace, "GNAT_TLA_ToLineWithinFromBuffer")

    # Select features from "To" line feature class that are outside "From" line buffer
    arcpy.SelectLayerByAttribute_management(lyrToLine, "SWITCH_SELECTION")
    fcToLineOutsideFromBuffer = arcpy.FeatureClassToFeatureClass_conversion(lyrToLine, tempWorkspace, "GNAT_TLA_ToLineOutsideFromBuffer")

    # Segment "From" line buffer polygon
    fcSegmentedBoundingPolygons = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_SegmentedBoundingPolygons")
    DividePolygonBySegment.main(fcFromLineTemp, fcFromLineBuffer, fcSegmentedBoundingPolygons)

    # Split points of "To" line at intersection of polygon segments
    fcIntersectSplitPoints = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_IntersectSplitPoints")
    arcpy.Intersect_analysis([fcToLineWithinFromBuffer,fcSegmentedBoundingPolygons],fcIntersectSplitPoints,output_type="POINT")
    fcSplitLines = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_SplitLines")
    arcpy.SplitLineAtPoint_management(fcToLineWithinFromBuffer,fcIntersectSplitPoints,fcSplitLines,"0.1 METERS")

    # Spatial join lines based on a common OID, as transferred by segmented polygon
    arcpy.AddMessage("GNAT TLA: Joining polygon segments")
    gis_tools.resetData(fcOutputLineNetwork)
    arcpy.SpatialJoin_analysis(fcSplitLines,
                               fcSegmentedBoundingPolygons,
                               fcOutputLineNetwork,
                               "JOIN_ONE_TO_ONE",
                               "KEEP_ALL",
                               match_option="WITHIN")
    arcpy.JoinField_management(fcOutputLineNetwork, "JOIN_FID", fcFromLineTemp, str(arcpy.Describe(fcFromLineTemp).OIDFieldName))

    # Append the "To" lines that were outside of the "From" line buffer, which will have NULL or zero values
    arcpy.env.extent = fcToLine # this was changed earlier in the process by  Divide Polygon by Segment script
    arcpy.Append_management([fcToLineOutsideFromBuffer], fcOutputLineNetwork, "NO_TEST")
    arcpy.AddMessage("GNAT TLA: Tool complete")

    return


# if __name__ == "__main__":
#     fcToLine = r"C:\JL\Testing\GNAT\Issue29\data2\To.shp"
#     fcFromLine = r"C:\JL\Testing\GNAT\Issue29\data2\From.shp"
#     fcOutputLineNetwork = r"C:\JL\Testing\GNAT\Issue29\data2\Output.shp"
#     tempWorkspace = r"C:\JL\Testing\GNAT\Issue29\data2\scratch.gdb"
#     main(fcFromLine, fcToLine, fcOutputLineNetwork, tempWorkspace)