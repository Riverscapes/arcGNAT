# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Transfer Linework Attributes Tool                              #
# Purpose:     Transfer attributes from one line layer to another             #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Version:     1.3                                                           #
# Modified:    2015-Aug-20                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import sys
import arcpy
import gis_tools
import DividePolygonBySegment

def main(fcFromLine,
         fcToLine,
         fieldBranchID, # Validate that both networks have the same BranchID field.
         fcOutputLineNetwork,
         tempWorkspace):
    
    ## Make Bounding Polygon
    fcFromLineBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_FromLineBuffer")
    arcpy.Buffer_analysis(fcFromLine,fcFromLineBuffer,"10 Meters","FULL","ROUND","ALL")
    fcToLineBuffer = gis_tools.newGISDatasetS(tempWorkspace,"GNAT_TLA_ToLineBuffer")
    arcpy.Buffer_analysis(fcToLine,fcToLineBuffer,"10 Meters","FULL","ROUND","ALL")
    fcUnionBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_UnionBuffer")
    arcpy.Union_analysis([fcToLineBuffer,fcFromLineBuffer],fcUnionBuffer)
    fcDissolveBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_DissolveBuffer")
    arcpy.Dissolve_management(fcUnionBuffer,fcDissolveBuffer)
    fcFinalBuffer = gis_tools.newGISDataset(tempWorkspace,fcDissolveBuffer)
    arcpy.EliminatePolygonPart_management(fcDissolveBuffer,fcFinalBuffer,"PERCENT",part_area_percent="99.9",part_option="CONTAINED_ONLY")

    ## If Branch Field Exists, process each branch seperately
    if fieldBranchID:
    
        ## Get list of Unique BranchIDs
        listBranchIDs = gis_tools.unique_values(fcFromLine,fieldBranchID)
        
        ## Loop Through BranchID's
        for branchID in listBranchIDs:
            lyrToLineBranch = gis_tools.newGISDataset("LAYER","lyrToLineBranch")
            lyrFromLineBranch = gis_tools.newGISDataset("LAYER","lyrFromLineBranch")

            whereTo = arcpy.AddFieldDelimiters(lyrToLineBranch,fieldBranchID) + " = " + str(branchID)
            whereFrom = arcpy.AddFieldDelimiters(lyrFromLineBranch,fieldBranchID) + " = " + str(branchID)
            arcpy.MakeFeatureLayer_management(fcToLine,lyrToLineBranch,whereTo)
            arcpy.MakeFeatureLayer_management(fcFromLine,lyrFromLineBranch,whereFrom)


            fcBoundingBranch = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_BoundingBranchPolygon_" + str(branchID))
            DividePolygonBySegment.main(lyrFromLineBranch,fcFinalBuffer,fcBoundingBranch,tempWorkspace)

            #Intersect
            fcIntersectBranch = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_IntersectToLineBranch_" + str(branchID))
            arcpy.Intersect_analysis([fcBoundingBranch,lyrToLine],fcIntersectBranch)

            # Join?

    else:

        # Segment Boundary Polygon in not segmented
        if bool_IsSegmented is not True:
            fcSegmentedBoundingPolygons = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_02_SegmentedBoundingPolygons")
            DividePolygonBySegment.main(fcFromLine,fcRawBoundingPolygon,fcSegmentedBoundingPolygons,tempWorkspace)
        else: 
            fcSegmentedBoundingPolygons = fcRawBoundingPolygon


    #if version == "OLD":    
    #    # Split Points of ToLine at intersection of Polygon Segments
    #    fcIntersectSplitPoints = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_03_IntersectSplitPoints")
    #    arcpy.Intersect_analysis([fcToLine,fcSegmentedBoundingPolygons],fcIntersectSplitPoints,output_type="POINT")

    #    fcSplitLines = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_04_SplitLines")
    #    arcpy.SplitLineAtPoint_management(fcToLine,fcIntersectSplitPoints,fcSplitLines,"2 METERS")

    #    # Spatial Join Lines based on common FID, as transfered by Segmented Polygon

    #    gis_tools.resetData(fcOutputLineNetwork)

    #    arcpy.SpatialJoin_analysis(fcSplitLines,
    #                               fcSegmentedBoundingPolygons,
    #                               fcOutputLineNetwork,
    #                               "JOIN_ONE_TO_ONE",
    #                               "KEEP_ALL",
    #                               match_option="WITHIN")

    #    arcpy.JoinField_management(fcOutputLineNetwork,
    #                               "JOIN_FID",
    #                               fcFromLine,
    #                               str(arcpy.Describe(fcFromLine).OIDFieldName))
    #else:

    
    return

if __name__ == "__main__":

    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3],
         sys.argv[4],
         sys.argv[5])