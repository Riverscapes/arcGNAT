# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Transfer Linework Attributes Tool                              #
# Purpose:     Transfer attributes from one line layer to another             #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              Jesse Langdon (jesse@southforkresearch.org                     #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-01-08                                                     #
# Version:     2.0 (Beta)                                                     #
# Modified:    2017-02-15                                                     #
#                                                                             #
# Copyright:   (c) Kelly Whitehead, Jesse Langdon                             #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python


# Import modules
import sys
import arcpy
import gis_tools
import DividePolygonBySegment

def main(fcFromLine,
         fcToLine,
         fcOutputLineNetwork,
         tempWorkspace):

    gis_tools.resetData(fcOutputLineNetwork)

    if tempWorkspace == '':
        tempWorkspace == "in_memory"

    # Make bounding polygon
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
    DividePolygonBySegment.main(fcFromLine,fcFinalBuffer,fcSegmentedBoundingPolygons)

    # Split points of "To" line at intersection of polygon segments
    fcIntersectSplitPoints = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_IntersectSplitPoints")
    arcpy.Intersect_analysis([fcToLine,fcSegmentedBoundingPolygons],fcIntersectSplitPoints,output_type="POINT")

    fcSplitLines = gis_tools.newGISDataset(tempWorkspace,"GNAT_TLA_SplitLines")
    arcpy.SplitLineAtPoint_management(fcToLine,fcIntersectSplitPoints,fcSplitLines,"0.1 METERS")

    # Spatial join lines based on a common FID, as transferred by segmented polygon
    gis_tools.resetData(fcOutputLineNetwork)

    arcpy.SpatialJoin_analysis(fcSplitLines,
                               fcSegmentedBoundingPolygons,
                               fcOutputLineNetwork,
                               "JOIN_ONE_TO_ONE",
                               "KEEP_ALL",
                               match_option="WITHIN")

    arcpy.JoinField_management(fcOutputLineNetwork, "JOIN_FID", fcFromLine, str(arcpy.Describe(fcFromLine).OIDFieldName))
    
    return

if __name__ == "__main__":
    # fcToLine = r"C:\JL\Testing\GNAT\TransferLineAttributes\input.gdb\seg1000m_entiat"
    # fcFromLine = r"C:\JL\Testing\GNAT\TransferLineAttributes\input.gdb\Entiat_EP_20160930"
    # fcOutputLineNetwork = r"C:\JL\Testing\GNAT\TransferLineAttributes\output.gdb\test_Entiat"
    # tempWorkspace = r"C:\JL\Testing\GNAT\TransferLineAttributes\scratch.gdb"
    # main(fcFromLine, fcToLine, fcOutputLineNetwork, tempWorkspace)

    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3],
         sys.argv[4],
         sys.argv[5])