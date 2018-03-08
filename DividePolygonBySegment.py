# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Divide Polygon By Segments Tool                                #
# Purpose:     Divides a channel or valley polygon by centerline segments.    #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Version:     1                                                              #
# Modified:    2015-Apr-27                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# !/usr/bin/env python

# # Import Modules # #
import sys
import arcpy
import gis_tools
import geometry_functions


# # Main Function # #
def main(fcInputCenterline,
         fcInputPolygon,
         fcSegmentedPolygons,
         dblPointDensity=10.0,
         dblJunctionBuffer=100.00):
    workspaceTemp = "in_memory"

    arcpy.env.OutputMFlag = "Disabled"
    arcpy.env.OutputZFlag = "Disabled"

    # Copy centerline to temporary workspace
    fcCenterline = gis_tools.newGISDataset(workspaceTemp, "GNAT_DPS_Centerline")
    arcpy.CopyFeatures_management(fcInputCenterline, fcCenterline)

    # Build Thiessan polygons
    arcpy.AddMessage("GNAT DPS: Building Thiessan polygons")
    arcpy.env.extent = fcInputPolygon  ## Set full extent to build Thiessan polygons over entire line network.
    arcpy.Densify_edit(fcCenterline, "DISTANCE", str(dblPointDensity) + " METERS")

    fcTribJunctionPoints = gis_tools.newGISDataset(workspaceTemp,
                                                   "GNAT_DPS_TribJunctionPoints")  # All Segment Junctions??
    arcpy.Intersect_analysis(fcCenterline, fcTribJunctionPoints, output_type="POINT")

    fcThiessanPoints = gis_tools.newGISDataset(workspaceTemp, "GNAT_DPS_ThiessanPoints")
    arcpy.FeatureVerticesToPoints_management(fcCenterline, fcThiessanPoints, "ALL")

    lyrThiessanPoints = gis_tools.newGISDataset("Layer", "lyrThiessanPoints")
    arcpy.MakeFeatureLayer_management(fcThiessanPoints, lyrThiessanPoints)
    arcpy.SelectLayerByLocation_management(lyrThiessanPoints, "INTERSECT", fcTribJunctionPoints,
                                           str(dblJunctionBuffer) + " METERS", "NEW_SELECTION")

    fcThiessanPoly = gis_tools.newGISDataset(workspaceTemp, "GNAT_DPS_ThiessanPoly")
    # arcpy.CreateThiessenPolygons_analysis(lyrThiessanPoints,fcThiessanPoly,"ONLY_FID")
    arcpy.CreateThiessenPolygons_analysis(lyrThiessanPoints, fcThiessanPoly, "ALL")

    # Clean polygons
    lyrInputPolygon = gis_tools.newGISDataset("Layer", "lyrInputPolygon")
    arcpy.MakeFeatureLayer_management(fcInputPolygon, lyrInputPolygon)
    arcpy.RepairGeometry_management(lyrInputPolygon, "KEEP_NULL")

    fcThiessanPolyClip = gis_tools.newGISDataset(workspaceTemp,"GNAT_DPS_TheissanPolyClip")
    arcpy.Clip_analysis(fcThiessanPoly,lyrInputPolygon,fcThiessanPolyClip)

    # Split the junction Thiessan polygons
    arcpy.AddMessage("GNAT DPS: Split junction Thiessan polygons")
    lyrTribThiessanPolys = gis_tools.newGISDataset("Layer", "lyrTribThiessanPolys")
    arcpy.MakeFeatureLayer_management(fcThiessanPolyClip, lyrTribThiessanPolys)
    arcpy.SelectLayerByLocation_management(lyrTribThiessanPolys, "INTERSECT", fcTribJunctionPoints,
                                           selection_type="NEW_SELECTION")

    fcSplitPoints = gis_tools.newGISDataset(workspaceTemp, "GNAT_DPS_SplitPoints")
    arcpy.Intersect_analysis([lyrTribThiessanPolys, fcCenterline], fcSplitPoints, output_type="POINT")

    arcpy.AddMessage("GNAT DPS: Moving starting vertices of junction polygons")
    geometry_functions.changeStartingVertex(fcTribJunctionPoints, lyrTribThiessanPolys)

    arcpy.AddMessage("GNAT DPS: Vertices moved")
    fcThiessanTribPolyEdges = gis_tools.newGISDataset(workspaceTemp, "GNAT_DPS_ThiessanTribPolyEdges")
    arcpy.FeatureToLine_management(lyrTribThiessanPolys, fcThiessanTribPolyEdges)

    fcSplitLines = gis_tools.newGISDataset(workspaceTemp, "GNAT_DPS_SplitLines")
    arcpy.SplitLineAtPoint_management(fcThiessanTribPolyEdges, fcSplitPoints, fcSplitLines, "0.1 METERS")

    fcMidPoints = gis_tools.newGISDataset(workspaceTemp, "GNAT_DPS_MidPoints")
    arcpy.FeatureVerticesToPoints_management(fcSplitLines, fcMidPoints, "MID")
    arcpy.Near_analysis(fcMidPoints, fcTribJunctionPoints, location="LOCATION")
    arcpy.AddXY_management(fcMidPoints)

    fcTribToMidLines = gis_tools.newGISDataset(workspaceTemp, "GNAT_DPS_TribToMidLines")
    arcpy.XYToLine_management(fcMidPoints,
                              fcTribToMidLines,
                              "POINT_X",
                              "POINT_Y",
                              "NEAR_X",
                              "NEAR_Y")

    ### Select polygons by centerline ###
    arcpy.AddMessage("GNAT DPS: Select polygons by centerline")
    fcThiessanEdges = gis_tools.newGISDataset(workspaceTemp, "GNAT_DPS_ThiessanEdges")
    arcpy.FeatureToLine_management(fcThiessanPolyClip, fcThiessanEdges)

    fcAllEdges = gis_tools.newGISDataset(workspaceTemp, "GNAT_DPS_AllEdges")
    arcpy.Merge_management([fcTribToMidLines, fcThiessanEdges, fcCenterline],
                           fcAllEdges)  # include fcCenterline if needed

    fcAllEdgesPolygons = gis_tools.newGISDataset(r"C:\GIS\GNAT\Sinuosity_Planform\Version01\Temp", "GNAT_DPS_AllEdgesPolygons")
    arcpy.FeatureToPolygon_management(fcAllEdges, fcAllEdgesPolygons)

    fcAllEdgesPolygonsClip = gis_tools.newGISDataset(r"C:\GIS\GNAT\Sinuosity_Planform\Version01\Temp", "GNAT_DPS_AllEdgesPolygonsClip")
    arcpy.Clip_analysis(fcAllEdgesPolygons, fcInputPolygon, fcAllEdgesPolygonsClip)

    fcPolygonsJoinCenterline = gis_tools.newGISDataset(r"C:\GIS\GNAT\Sinuosity_Planform\Version01\Temp",
                                                       "GNAT_DPS_PolygonsJoinCenterline")
    arcpy.SpatialJoin_analysis(fcAllEdgesPolygonsClip,
                               fcCenterline,
                               fcPolygonsJoinCenterline,
                               "JOIN_ONE_TO_MANY",
                               "KEEP_ALL",
                               match_option="SHARE_A_LINE_SEGMENT_WITH")

    fcPolygonsDissolved = gis_tools.newGISDataset(r"C:\GIS\GNAT\Sinuosity_Planform\Version01\Temp",
                                                  "GNAT_DPS_PolygonsDissolved")
    arcpy.Dissolve_management(fcPolygonsJoinCenterline,
                              fcPolygonsDissolved,
                              "InputID", #"FromID",
                              multi_part="SINGLE_PART")

    lyrPolygonsDissolved = gis_tools.newGISDataset("Layer", "lyrPolygonsDissolved")
    arcpy.MakeFeatureLayer_management(fcPolygonsDissolved, lyrPolygonsDissolved)
    arcpy.SelectLayerByAttribute_management(lyrPolygonsDissolved, "NEW_SELECTION", """ "InputID" IS NULL """)

    arcpy.Eliminate_management(lyrPolygonsDissolved, fcSegmentedPolygons, "LENGTH")

    arcpy.AddMessage("GNAT DPS: Tool complete")
    return


# # Run as script # #
if __name__ == "__main__":
    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3],
         sys.argv[4],
         sys.argv[5])
