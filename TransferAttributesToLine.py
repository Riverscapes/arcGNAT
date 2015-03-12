# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Transfer Linework Attributes Tool                              #
# Purpose:     Transfer attributes from one line layer to another             #
#                                                                             #
# Author:      Kelly Whitehead                                                #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Version:     0.1          Modified: 2015-Jan-08                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import sys
import arcpy
import gis_tools
import DividePolygonBySegment

def main(fcFromLine,fcToLine,fcRawBoundingPolygon,bool_IsSegmented,fcOutputLineNetwork):
    
    workspaceTemp=arcpy.env.scratchWorkspace
    
    fcTempLine = gis_tools.newGISDataset(workspaceTemp,"Transfer_01_TempLine")
    arcpy.CopyFeatures_management(fcFromLine,fcTempLine)
    
    if bool_IsSegmented == False:
        fcSegmentedBoundingPolygons = gis_tools.newGISDataset(workspaceTemp,"Transfer_02_SegmentedBoundingPolygons")
        DividePolygonBySegment.main(fcFromLine,fcRawBoundingPolygon,fcSegmentedBoundingPolygons,workspaceTemp)
    else: 
        fcSegmentedBoundingPolygons = fcRawBoundingPolygon

    fcIntersectSplitPoints = gis_tools.newGISDataset(workspaceTemp,"Transfer_03_IntersectSplitPoints")
    arcpy.Intersect_analysis([fcToLine,fcSegmentedBoundingPolygons],fcIntersectSplitPoints,output_type="POINT")

    fcSplitLines = gis_tools.newGISDataset(workspaceTemp,"Transfer_04_SplitLines")
    arcpy.SplitLineAtPoint_management(fcToLine,fcIntersectSplitPoints,fcSplitLines,"2 METERS")

    #fcSplitLinesJoinFID = gis_tools.newGISDataset(workspaceTemp,"Transfer_05_SplitLinesJoinFID")
    if arcpy.Exists(fcOutputLineNetwork):
        arcpy.Delete_management(fcOutputLineNetwork)
    fcSplitLinesJoinFID = fcOutputLineNetwork

    arcpy.SpatialJoin_analysis(fcSplitLines,
                               fcSegmentedBoundingPolygons,
                               fcSplitLinesJoinFID,
                               "JOIN_ONE_TO_ONE",
                               "KEEP_ALL",
                               #"""JOIN_FID "JOIN_FID" true true false 4 Long 0 0 ,First,#,""" + str(fcSegmentedBoundingPolygons) + """,JOIN_FID,-1,-1""",
                               match_option="WITHIN"
                               )

    arcpy.JoinField_management(fcSplitLinesJoinFID,
                               "JOIN_FID",
                               fcFromLine,
                               "OBJECTID",
                               )
    
    return

if __name__ == "__main__":

    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3],
         sys.argv[4]
         )
