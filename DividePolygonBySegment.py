# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Divide Polygon By Segments Tool                                #
# Purpose:     Divides a channel or valley polygon by centerline segments.    #
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
import ChangeStartingVertex

def main(fcInputCenterline,fcInputPolygon,fcSegmentedPolygons,workspaceTemp=arcpy.env.scratchWorkspace,dblPointDensity=10.0,dblJunctionBuffer=120.00):
    
    arcpy.AddMessage("RiverStyles PolygonSegmentation Tool")
    arcpy.AddMessage("Saving Polygon Results to: " + fcSegmentedPolygons)
    arcpy.AddMessage("Saving Temporary Files to: " + workspaceTemp)

    ## Copy Centerline to Temp Workspace
    fcCenterline = gis_tools.newGISDataset(workspaceTemp,"Centerline")
    arcpy.CopyFeatures_management(fcInputCenterline,fcCenterline)

    arcpy.env.extent = fcInputCenterline

    arcpy.Densify_edit(fcCenterline,"DISTANCE",dblPointDensity)

    fcTribJunctionPoints = gis_tools.newGISDataset(workspaceTemp,"TribJunctionPoints") # All Segment Junctions??
    gis_tools.findSegmentJunctions(fcCenterline,fcTribJunctionPoints,"ALL")

    fcThiessanPoints = gis_tools.newGISDataset(workspaceTemp,"ThiessanPoints")
    arcpy.FeatureVerticesToPoints_management(fcCenterline,fcThiessanPoints,"ALL")

    lyrThiessanPoints = gis_tools.newGISDataset("Layer","lyrThiessanPoints")
    arcpy.MakeFeatureLayer_management(fcThiessanPoints,lyrThiessanPoints)
    arcpy.SelectLayerByLocation_management(lyrThiessanPoints,"INTERSECT",fcTribJunctionPoints,str(dblJunctionBuffer)+ " METERS","NEW_SELECTION")

    fcThiessanPoly = gis_tools.newGISDataset(workspaceTemp,"ThiessanPoly")
    arcpy.CreateThiessenPolygons_analysis(lyrThiessanPoints,fcThiessanPoly,"ONLY_FID")
    fcThiessanPolyClip = gis_tools.newGISDataset(workspaceTemp,"TheissanPolyClip")
    arcpy.Clip_analysis(fcThiessanPoly,fcInputPolygon,fcThiessanPolyClip)

    ### Code to Split the Junction Thiessan Polys ###
    
    lyrTribThiessanPolys = gis_tools.newGISDataset("Layer","lyrTribThiessanPolys")
    arcpy.MakeFeatureLayer_management(fcThiessanPolyClip,lyrTribThiessanPolys)
    arcpy.SelectLayerByLocation_management(lyrTribThiessanPolys,"INTERSECT",fcTribJunctionPoints,selection_type="NEW_SELECTION")

    fcSplitPoints = gis_tools.newGISDataset(workspaceTemp,"SplitPoints")
    arcpy.Intersect_analysis([lyrTribThiessanPolys,fcCenterline],fcSplitPoints,output_type="POINT")

    ChangeStartingVertex.main(fcTribJunctionPoints,lyrTribThiessanPolys)

    fcThiessanTribPolyEdges = gis_tools.newGISDataset(workspaceTemp,"ThiessanTribPolyEdges")
    arcpy.FeatureToLine_management(lyrTribThiessanPolys,fcThiessanTribPolyEdges)

    fcSplitLines = gis_tools.newGISDataset(workspaceTemp,"SplitLines")
    arcpy.SplitLineAtPoint_management(fcThiessanTribPolyEdges,fcSplitPoints,fcSplitLines,"0.1 METERS")

    fcMidPoints = gis_tools.newGISDataset(workspaceTemp,"MidPoints")
    arcpy.FeatureVerticesToPoints_management(fcSplitLines,fcMidPoints,"MID")
    arcpy.Near_analysis(fcMidPoints,fcTribJunctionPoints,location="LOCATION")
    arcpy.AddXY_management(fcMidPoints)

    fcTribToMidLines = gis_tools.newGISDataset(workspaceTemp,"TribToMidLines")
    arcpy.XYToLine_management(fcMidPoints,
                              fcTribToMidLines,
                              "POINT_X",
                              "POINT_Y",
                              "NEAR_X",
                              "NEAR_Y")

    ### Select Polys by Centerline ###

    fcThiessanEdges = gis_tools.newGISDataset(workspaceTemp,"ThiessanEdges")
    arcpy.FeatureToLine_management(fcThiessanPolyClip,fcThiessanEdges)

    fcAllEdges = gis_tools.newGISDataset(workspaceTemp,"AllEdges")
    arcpy.Merge_management([fcTribToMidLines,fcThiessanEdges,fcCenterline],fcAllEdges)# include fcCenterline if needed

    fcAllEdgesPolygons = gis_tools.newGISDataset(workspaceTemp,"AllEdgesPolygons")
    arcpy.FeatureToPolygon_management(fcAllEdges,fcAllEdgesPolygons)

    fcAllEdgesPolygonsClip = gis_tools.newGISDataset(workspaceTemp,"AllEdgesPolygonsClip")
    arcpy.Clip_analysis(fcAllEdgesPolygons,fcInputPolygon,fcAllEdgesPolygonsClip)

    fcPolygonsJoinCenterline = gis_tools.newGISDataset(workspaceTemp,"PolygonsJoinCenterline")
    arcpy.SpatialJoin_analysis(fcAllEdgesPolygonsClip,
                               fcCenterline,
                               fcPolygonsJoinCenterline,
                               "JOIN_ONE_TO_MANY",
                               "KEEP_ALL",
                               match_option="SHARE_A_LINE_SEGMENT_WITH")

    fcPolygonsDissolved = gis_tools.newGISDataset(workspaceTemp,"PolygonsDissolved")
    arcpy.Dissolve_management(fcPolygonsJoinCenterline,
                              fcPolygonsDissolved,
                              "JOIN_FID",
                              multi_part="SINGLE_PART")

    #fcSegmentedPolygons = gis_tools.newGISDataset(workspaceOutput,"SegmentedPolygons")
    lyrPolygonsDissolved = gis_tools.newGISDataset("Layer","lyrPolygonsDissolved")
    arcpy.MakeFeatureLayer_management(fcPolygonsDissolved,lyrPolygonsDissolved)
    arcpy.SelectLayerByAttribute_management(lyrPolygonsDissolved,"NEW_SELECTION",""" "JOIN_FID" = -1 """)

    arcpy.Eliminate_management(lyrPolygonsDissolved,fcSegmentedPolygons,"LENGTH")

    return

if __name__ == "__main__":

    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3],
         sys.argv[4])