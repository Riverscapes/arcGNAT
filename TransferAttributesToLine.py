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
    


    gis_tools.resetData(fcOutputLineNetwork)

    ## If Branch Field Exists, process each branch seperately
    if fieldBranchID:
    
        ## Get list of Unique BranchIDs
        listBranchIDs = gis_tools.unique_values(fcFromLine,fieldBranchID)
        list_fcIntersectBranches = []
        ## Loop Through BranchID's
        for branchID in listBranchIDs:
            arcpy.env.extent = "MAXOF"
            arcpy.AddMessage("GNAT TLA | Branch: " + str(branchID))
            lyrToLineBranch = gis_tools.newGISDataset("LAYER","lyrToLineBranch")
            lyrFromLineBranch = gis_tools.newGISDataset("LAYER","lyrFromLineBranch")

            whereTo = arcpy.AddFieldDelimiters(lyrToLineBranch,fieldBranchID) + " = " + str(branchID)
            whereFrom = arcpy.AddFieldDelimiters(lyrFromLineBranch,fieldBranchID) + " = " + str(branchID)
            arcpy.MakeFeatureLayer_management(fcToLine,lyrToLineBranch,whereTo)
            arcpy.MakeFeatureLayer_management(fcFromLine,lyrFromLineBranch,whereFrom)

            ## Generate Bounding Polygon for Branch
            fcFromLineBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_FromLineBuffer_" + str(branchID))
            arcpy.Buffer_analysis(lyrFromLineBranch,fcFromLineBuffer,"10 Meters","FULL","ROUND","ALL")
            fcToLineBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_ToLineBuffer_" + str(branchID))
            arcpy.Buffer_analysis(lyrToLineBranch,fcToLineBuffer,"10 Meters","FULL","ROUND","ALL")
            fcUnionBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_UnionBuffer_" + str(branchID))
            arcpy.Union_analysis([fcToLineBuffer,fcFromLineBuffer],fcUnionBuffer)
            fcDissolveBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_DissolveBuffer_" + str(branchID))
            arcpy.Dissolve_management(fcUnionBuffer,fcDissolveBuffer)
            fcFinalBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_FinalBuffer_" + str(branchID))
            arcpy.EliminatePolygonPart_management(fcDissolveBuffer,fcFinalBuffer,"PERCENT",part_area_percent="99.9",part_option="CONTAINED_ONLY")

            fcBoundingBranch = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_BoundingBranchPolygon_" + str(branchID))
            DividePolygonBySegment.main(lyrFromLineBranch,fcFinalBuffer,fcBoundingBranch,tempWorkspace)

            fcBoundingBranchWithAttributes = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_BoundingBranchPolygonAttributes_" + str(branchID))
            arcpy.SpatialJoin_analysis(fcBoundingBranch,
                        lyrFromLineBranch,
                        fcBoundingBranchWithAttributes,
                        "JOIN_ONE_TO_ONE",
                        "KEEP_ALL",
                        match_option="CONTAINS")

            #Intersect
            fcIntersectBranch = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_IntersectToLineBranch_" + str(branchID))
            arcpy.Intersect_analysis([fcBoundingBranchWithAttributes,lyrToLineBranch],fcIntersectBranch)

            listFields = arcpy.ListFields(fcIntersectBranch,"FID_GNAT_TLA_*")
            for field in listFields:
                arcpy.DeleteField_management(fcIntersectBranch,field.name)
            
            # Join Attributes
            #fcIntersectBranchWithAttributes = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_IntersectToLineBranchAttributes_" + str(branchID))
            #arcpy.SpatialJoin_analysis(fcIntersectBranch,
            #                       fcBoundingBranch,
            #                       fcIntersectBranchWithAttributes,
            #                       "JOIN_ONE_TO_ONE",
            #                       "KEEP_ALL",
            #                       match_option="WITHIN")

            #arcpy.JoinField_management(fcIntersectBranchWithAttributes,
            #                       "JOIN_FID",
            #                       fcFromLine,
            #                       str(arcpy.Describe(fcFromLine).OIDFieldName))
            list_fcIntersectBranches.append(fcIntersectBranch)
        
        arcpy.env.extent = "MAXOF"
        arcpy.Merge_management(list_fcIntersectBranches,fcOutputLineNetwork)
    else:

        ## Make Bounding Polygon
        fcFromLineBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_FromLineBuffer")
        arcpy.Buffer_analysis(fcFromLine,fcFromLineBuffer,"10 Meters","FULL","ROUND","ALL")
        fcToLineBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_ToLineBuffer")
        arcpy.Buffer_analysis(fcToLine,fcToLineBuffer,"10 Meters","FULL","ROUND","ALL")
        fcUnionBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_UnionBuffer")
        arcpy.Union_analysis([fcToLineBuffer,fcFromLineBuffer],fcUnionBuffer)
        fcDissolveBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_DissolveBuffer")
        arcpy.Dissolve_management(fcUnionBuffer,fcDissolveBuffer)
        fcFinalBuffer = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_FinalBuffer")
        arcpy.EliminatePolygonPart_management(fcDissolveBuffer,fcFinalBuffer,"PERCENT",part_area_percent="99.9",part_option="CONTAINED_ONLY")

        fcSegmentedBoundingPolygons = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_SegmentedBoundingPolygons")
        DividePolygonBySegment.main(fcFromLine,fcFinalBuffer,fcSegmentedBoundingPolygons,tempWorkspace)

        # Split Points of ToLine at intersection of Polygon Segments
        fcIntersectSplitPoints = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_IntersectSplitPoints")
        arcpy.Intersect_analysis([fcToLine,fcSegmentedBoundingPolygons],fcIntersectSplitPoints,output_type="POINT")

        fcSplitLines = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_SplitLines")
        arcpy.SplitLineAtPoint_management(fcToLine,fcIntersectSplitPoints,fcSplitLines,"0.1 METERS")

        # Spatial Join Lines based on common FID, as transfered by Segmented Polygon

        gis_tools.resetData(fcOutputLineNetwork)

        arcpy.SpatialJoin_analysis(fcSplitLines,
                                   fcSegmentedBoundingPolygons,
                                   fcOutputLineNetwork,
                                   "JOIN_ONE_TO_ONE",
                                   "KEEP_ALL",
                                   match_option="WITHIN")

        arcpy.JoinField_management(fcOutputLineNetwork,
                                   "JOIN_FID",
                                   fcFromLine,
                                   str(arcpy.Describe(fcFromLine).OIDFieldName))

    
    return

if __name__ == "__main__":

    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3],
         sys.argv[4],
         sys.argv[5])