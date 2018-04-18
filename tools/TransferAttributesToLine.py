# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Transfer Attributes Tool                                       #
# Purpose:     Transfer attributes from one polyline feature class to another #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              Jesse Langdon (jesse@southforkresearch.org)                    #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Modified:    2018-April-13                                                  #
#                                                                             #
# Copyright:   (c) South Fork Research, Inc. 2018                             #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


import arcpy
from lib import gis_tools
from tools import DividePolygonBySegment


def empty_attributes(fc, to_fields):
    """
    Adds default values to attribute fields for features present in the 'From' network and
    not the 'To' network feature class
    :param fc: network feature class
    :param to_fields: attribute fields from the 'To' network feature class
    """
    from_fields = [f for f in arcpy.ListFields(fc) if f.name not in to_fields]
    for field in from_fields:
        with arcpy.da.UpdateCursor(fc, [field.name]) as cursor:
            for row in cursor:
                if field.type == "String":
                    row[0] = "-99999"
                    cursor.updateRow(row)
                if field.type == "Double":
                    row[0] = -99999
                    cursor.updateRow(row)
                if field.type == "Integer":
                    row[0] = -99999
                    cursor.updateRow(row)
                if field.type == "SmallInteger":
                    row[0] = -999
                    cursor.updateRow(row)
    return


def transfer_fields(fc):
    """
    Returns a list of fields names (minus the geometry and OID fields) to be transferred between networks
    :param fc: network feature class
    :return: list of field names, and string version of that list
    """
    listFieldObjects = arcpy.ListFields(fc)
    listFieldNames = [f.name for f in listFieldObjects if f.type != "OID" and f.type != "Geometry"]
    strFieldNames = "; ".join(listFieldNames)
    return listFieldNames, strFieldNames


def plot_junction_points(line_lyr, network_type):
    """
    Dissolves a network polyline feature class into single part features, intersects the dissolved network
    with itself, and returns a junction point (i.e. tributarty confluence) feature class.
    :param fc: network polyine feature class
    :return: point feature class
    """
    line_dslv = "in_memory\\line_dslv"
    gis_tools.newGISDataset("in_memory", line_dslv)
    arcpy.Dissolve_management(line_lyr, line_dslv, "#", "#", "SINGLE_PART")
    pnt_junctions = "in_memory\\{0}_pnt_junctions".format(network_type)
    gis_tools.newGISDataset("in_memory", pnt_junctions)
    arcpy.Intersect_analysis(line_dslv, pnt_junctions, output_type="POINT")
    arcpy.AddXY_management(pnt_junctions)
    return pnt_junctions


def list_oids(in_fc, oid_field):
    list_oid = []
    with arcpy.da.SearchCursor(in_fc, oid_field) as cursor:
        for row in cursor:
            list_oid.append(row[0])
    return list_oid


def snap_junction_points(from_line_lyr, to_line_lyr, search_distance):
    """
    Shifts junction points (i.e. tributary confluences) in the 'From' network to same coordinates
    of junction points in the 'To' network, found within a user-specified search distance.
    :param from_line_lyr: polyline layer representing 'From' stream network
    :param to_line_lyr: polyline layer representing 'To' stream network
    :param search_distance: buffer distance around each 'To' junction point, in meters
    :return:
    """
    arcpy.AddMessage("GNAT TLA: snapping junction points in 'From' network to 'To' network")

    list_field_objects = arcpy.ListFields(from_line_lyr)
    list_from_fields = [f.name for f in list_field_objects if f.type != "OID" and f.type != "Geometry"]

    # Plot junction points for 'From' and 'To' stream networks
    from_junction_pnts = plot_junction_points(from_line_lyr, "from")
    to_junction_pnts = plot_junction_points(to_line_lyr, "to")

    lyr_from_junc_pnts = gis_tools.newGISDataset("Layer", "lyr_from_junc_pnts")
    arcpy.MakeFeatureLayer_management(from_junction_pnts, lyr_from_junc_pnts)

    from_line_oidfield = arcpy.Describe(from_line_lyr).OIDFieldName
    list_from_oid = list_oids(lyr_from_junc_pnts, from_line_oidfield)

    for oid in list_from_oid:
        arcpy.SelectLayerByAttribute_management(lyr_from_junc_pnts, "NEW_SELECTION", """"{0}" = {1}""".format(from_line_oidfield, oid))
        arcpy.SelectLayerByLocation_management(from_line_lyr, "INTERSECT", lyr_from_junc_pnts, "#", "NEW_SELECTION")
        from_vrtx_adj = gis_tools.newGISDataset(temp_wspace, "vrtx_adj")
        arcpy.FeatureVerticesToPoints_management(from_line_lyr, from_vrtx_adj, point_location="ALL")
        arcpy.AddXY_management(from_vrtx_adj)
        from_vrtx_lyr = gis_tools.newGISDataset("Layer", "from_vrtx_lyr")
        arcpy.MakeFeatureLayer_management(from_vrtx_adj, from_vrtx_lyr)
        arcpy.Near_analysis(from_vrtx_lyr, to_junction_pnts, search_distance, "LOCATION")
        arcpy.SelectLayerByLocation_management(from_vrtx_lyr, "INTERSECT", lyr_from_junc_pnts, "#", "NEW_SELECTION")
        # Update Point_X and Point_Y fields with coordinates of nearest "To" junction point
        arcpy.CalculateField_management(from_vrtx_lyr, "POINT_X", "!NEAR_X!", "PYTHON_9.3")
        arcpy.CalculateField_management(from_vrtx_lyr, "POINT_Y", "!NEAR_Y!", "PYTHON_9.3")
        arcpy.MakeXYEventLayer_management(from_vrtx_lyr, "POINT_X", "POINT_Y", "xy_events", from_vrtx_lyr)
        xy_events_pnt = gis_tools.newGISDataset(temp_wspace, "xy_events_pnt")
        arcpy.CopyFeatures_management("xy_events", xy_events_pnt)
        xy_events_lyr = gis_tools.newGISDataset("Layer", "xy_events_lyr")
        arcpy.MakeFeatureLayer_management(xy_events_pnt, xy_events_lyr)
        adj_from_line = gis_tools.newGISDataset(temp_wspace, "adj_from_line")
        arcpy.PointsToLine_management("xy_events", adj_from_line, "ORIG_FID")
        arcpy.JoinField_management(adj_from_line, "ORIG_FID", from_line_lyr, from_line_oidfield, list_from_fields)
        arcpy.DeleteFeatures_management(from_line_lyr)
        arcpy.Append_management(adj_from_line, from_line_lyr, "NO_TEST")
        arcpy.AddMessage("Junction {} complete...".format(oid))
    return


def main(fcFromLine,
         fcToLine,
         fcOutputLineNetwork,
         searchDistance,
         tempWorkspace):

    # Environment settings
    arcpy.env.overwriteOutput = True
    arcpy.env.outputMFlag = "Disabled"
    arcpy.env.outputZFlag = "Disabled"
    arcpy.env.qualifiedFieldNames = False

    arcpy.AddMessage("GNAT TLA: starting transfer process...")

    gis_tools.resetData(fcOutputLineNetwork)
    fcFromLineTemp = gis_tools.newGISDataset(tempWorkspace, "GNAT_TLA_FromLineTemp")
    fcToLineTemp = gis_tools.newGISDataset(tempWorkspace, "GNAT_TLA_ToLineTemp")
    arcpy.MakeFeatureLayer_management(fcFromLine, "lyrFromLine")
    arcpy.MakeFeatureLayer_management(fcToLine, "lyrToLine")
    arcpy.CopyFeatures_management("lyrFromLine", fcFromLineTemp)
    arcpy.CopyFeatures_management("lyrToLine", fcToLineTemp)

    # Add a unique ID for the "From" line feature class
    from_oid = arcpy.Describe(fcFromLineTemp).OIDFieldName
    arcpy.AddField_management(fcFromLineTemp, "FromID", "LONG")
    arcpy.CalculateField_management(fcFromLineTemp, "FromID", "!{0}!".format(from_oid), "PYTHON_9.3")

    # Snap "From" line network to "To" line network
    lyrFromLineTemp = gis_tools.newGISDataset("Layer", "lyrFromLineTemp")
    lyrToLineTemp = gis_tools.newGISDataset("Layer", "lyrToLineTemp")
    arcpy.MakeFeatureLayer_management(fcFromLineTemp, lyrFromLineTemp)
    arcpy.MakeFeatureLayer_management(fcToLineTemp, lyrToLineTemp)
    snap_junction_points(lyrFromLineTemp, lyrToLineTemp, searchDistance)

    # Make bounding polygon for "From" line feature class
    arcpy.AddMessage("GNAT TLA: Create buffer polygon around 'From' network")
    fcFromLineBuffer = gis_tools.newGISDataset(tempWorkspace, "GNAT_TLA_FromLineBuffer")
    arcpy.Buffer_analysis(lyrFromLineTemp,fcFromLineBuffer,"{0} Meters".format(searchDistance * 3), "FULL", "ROUND", "ALL")
    fcFromLineBufDslv = gis_tools.newGISDataset(tempWorkspace, "GNAT_TLA_FromLineBUfDslv")
    arcpy.AddMessage("GNAT TLA: Dissolve buffer")
    arcpy.Dissolve_management(fcFromLineBuffer, fcFromLineBufDslv)

    # Select features from "To" line feature class that are inside "From" line buffer
    arcpy.AddMessage("GNAT TLA: Select 'To' line features inside 'From' buffer")
    lyrFromLineBuffer = gis_tools.newGISDataset("Layer", "lyrFromLineBuffer")
    arcpy.MakeFeatureLayer_management(fcFromLineBufDslv, lyrFromLineBuffer)
    lyrToLine = gis_tools.newGISDataset("Layer", "lyrToLine")
    arcpy.MakeFeatureLayer_management(fcToLine, lyrToLine)
    arcpy.SelectLayerByLocation_management(lyrToLine, "WITHIN", lyrFromLineBuffer, "#", "NEW_SELECTION")
    fcToLineWithinFromBuffer = arcpy.FeatureClassToFeatureClass_conversion(lyrToLine, tempWorkspace, "GNAT_TLA_ToLineWithinFromBuffer")

    # Select features from "To" line feature class that are outside "From" line buffer
    arcpy.SelectLayerByAttribute_management(lyrToLine, "SWITCH_SELECTION")
    fcToLineOutsideFromBuffer = arcpy.FeatureClassToFeatureClass_conversion(lyrToLine, tempWorkspace, "GNAT_TLA_ToLineOutsideFromBuffer")

    # Segment "From" line buffer polygon
    arcpy.AddMessage("GNAT TLA: Segmenting 'From' line buffer polygon")
    fcSegmentedBoundingPolygons = gis_tools.newGISDataset(tempWorkspace, "GNAT_TLA_SegmentedBoundingPolygons")
    DividePolygonBySegment.main(lyrFromLineTemp, fcFromLineBuffer, fcSegmentedBoundingPolygons, 10.0, 150.0)

    # Split points of "To" line at intersection of polygon segments
    arcpy.AddMessage("GNAT TLA: Split 'To' line features")
    fcIntersectSplitPoints = gis_tools.newGISDataset(tempWorkspace, "GNAT_TLA_IntersectSplitPoints")
    arcpy.Intersect_analysis([fcToLineWithinFromBuffer, fcSegmentedBoundingPolygons], fcIntersectSplitPoints, output_type="POINT")
    fcSplitLines = gis_tools.newGISDataset(tempWorkspace, "GNAT_TLA_SplitLines")
    arcpy.SplitLineAtPoint_management(fcToLineWithinFromBuffer, fcIntersectSplitPoints, fcSplitLines, "0.1 METERS")

    # # Spatial join lines based on a common field, as transferred by segmented polygon
    # arcpy.AddMessage("GNAT TLA: Joining polygon segments")
    # arcpy.SpatialJoin_analysis(fcSplitLines,
    #                            fcSegmentedBoundingPolygons,
    #                            fcOutputLineNetwork,
    #                            "JOIN_ONE_TO_ONE",
    #                            "KEEP_ALL",
    #                            match_option="WITHIN")
    # arcpy.JoinField_management(fcOutputLineNetwork, "FromID", fcFromLineTemp, "FromID")

    # instead of spatial join, use Transfer Attributes tool
    arcpy.AddMessage("GNAT TLA: Transferring attributes")
    listFromFieldNames, strFromFieldNames = transfer_fields(fcFromLine)
    arcpy.MakeFeatureLayer_management(fcSplitLines, "lyrSplitLines")
    arcpy.CopyFeatures_management("lyrSplitLines", fcOutputLineNetwork)
    arcpy.MakeFeatureLayer_management(fcOutputLineNetwork, "lyrOutputLineNetwork")
    arcpy.TransferAttributes_edit(lyrFromLineTemp, "lyrOutputLineNetwork", listFromFieldNames, "100 Meters")

    # Append the "To" lines that were outside of the "From" line buffer, which will have NULL or zero values
    arcpy.env.extent = fcToLine # changed earlier in the workflow in DividePolygonBySegment module
    arcpy.Append_management([fcToLineOutsideFromBuffer], fcOutputLineNetwork, "NO_TEST")

    # Change values of "From" features to -99999 if no "To" features to transfer to.
    arcpy.MakeFeatureLayer_management(fcOutputLineNetwork, "lyrOutputLineNetwork")
    arcpy.SelectLayerByLocation_management("lyrOutputLineNetwork", "ARE_IDENTICAL_TO", fcToLineOutsideFromBuffer, "#", "NEW_SELECTION")
    to_fields = [f.name for f in arcpy.ListFields(fcToLine)]
    empty_attributes("lyrOutputLineNetwork", to_fields)
    arcpy.SelectLayerByAttribute_management("lyrOutputLineNetwork", "CLEAR_SELECTION")

    arcpy.AddMessage("GNAT TLA: Tool complete")

    return


# TEST
if __name__ == "__main__":
    from_line = r'C:\JL\Testing\arcGNAT\TransferLineAttributes\input\wen_24k_sel.shp'
    to_line = r'C:\JL\Testing\arcGNAT\TransferLineAttributes\input\wen_100k_sel.shp'
    output_line = r'C:\JL\Testing\arcGNAT\TransferLineAttributes\output\wen_24k_to_100k.shp'
    search_dist = 50
    temp_wspace = r'C:\JL\Testing\arcGNAT\TransferLineAttributes\scratch.gdb'
    main(from_line, to_line, output_line, search_dist, temp_wspace)

# def vertex_type(line_lyr):
#     """
#     Converts line vertices to points, assigns start and end node types as attribute field
#     :param line_lyr: network line layer
#     :return: point feature class with added node type attribute field
#     """
#     temp_workspace = r'C:\JL\Testing\arcGNAT\TransferLineAttributes\scratch.gdb'
#     vrtx_all = gis_tools.newGISDataset(temp_workspace, "vrtx_all")
#     vrtx_start = gis_tools.newGISDataset(temp_workspace, "vrtx_start")
#     vrtx_end = gis_tools.newGISDataset(temp_workspace, "vrtx_end")
#     arcpy.FeatureVerticesToPoints_management(line_lyr, vrtx_all, point_location="ALL")
#     arcpy.AddXY_management(vrtx_all)
#     vrtx_all_lyr = gis_tools.newGISDataset("Layer", "vrtx_all_lyr")
#     arcpy.MakeFeatureLayer_management(vrtx_all, vrtx_all_lyr)
#     arcpy.AddField_management(vrtx_all_lyr, "node_type", "TEXT", "#", "#", 6)
#     arcpy.FeatureVerticesToPoints_management(line_lyr, vrtx_start, point_location="START")
#     arcpy.FeatureVerticesToPoints_management(line_lyr, vrtx_end, point_location="END")
#     arcpy.SelectLayerByLocation_management(vrtx_all_lyr, "INTERSECT", vrtx_start, "#", "NEW_SELECTION")
#     arcpy.CalculateField_management(vrtx_all_lyr, "node_type", '"START"', "PYTHON_9.3")
#     arcpy.SelectLayerByAttribute_management(vrtx_all_lyr, "CLEAR_SELECTION")
#     arcpy.SelectLayerByLocation_management(vrtx_all_lyr, "INTERSECT", vrtx_end, "#", "NEW_SELECTION")
#     arcpy.CalculateField_management(vrtx_all_lyr, "node_type", '"END"', "PYTHON_9.3")
#     arcpy.SelectLayerByAttribute_management(vrtx_all_lyr, "CLEAR_SELECTION")
#     return vrtx_all_lyr