# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Valley Planform Tool                                           #
# Purpose:     Calculates valley planform along reaches in a stream network.  #
#              Also calculates sinuosity along reaches in stream and valley   #
#              network.                                                       #
#                                                                             #
# Authors:     Kelly Whitehead (kelly@southforkresearch.org)                  #
#              Jesse Langdon (jesse@southforkresearch.org)                    #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Modified:    2017-Nov-28                                                    #
#                                                                             #
# Copyright:   (c) South Fork Research, Inc. 2017                             #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

import arcpy
import gis_tools
import Sinuosity
import TransferAttributesToLine


def Old_main(fcChannelSinuosity,
         fcValleyCenterline,
         fcValleyBottomPolygon,
         outputFCSinuosityValley,
         outputFCPlanform,
         workspaceTemp="in_memory"):
    
    # Set workspace and reset modules
    reload(TransferAttributesToLine)
    reload(Sinuosity)

    lyrChannelSinuosity = "lyrChannelSinuosity"
    arcpy.MakeFeatureLayer_management(fcChannelSinuosity, lyrChannelSinuosity)
    tmpChannelSinuosity = workspaceTemp + r"\tmpChannelSinuosity"
    arcpy.CopyFeatures_management(lyrChannelSinuosity, tmpChannelSinuosity)

    fieldInputID = gis_tools.resetField(tmpChannelSinuosity, "InputID", "DOUBLE")
    arcpy.CalculateField_management(tmpChannelSinuosity,
                                    fieldInputID,
                                    "!" + arcpy.Describe(tmpChannelSinuosity).OIDFieldName + "!",
                                    "PYTHON_9.3")

    # Calculate centerline sinuosity for each valley centerline segment
    if arcpy.Exists(outputFCSinuosityValley):
        arcpy.Delete_management(outputFCSinuosityValley)
    Sinuosity.main(fcValleyCenterline, "V_Sin", workspaceTemp)
    # write the valley centerline sinuosity feature class to disk
    arcpy.CopyFeatures_management(fcValleyCenterline, outputFCSinuosityValley)

    # Transfer attributes to channel sinuosity polyline feature class
    if arcpy.Exists(outputFCPlanform):
        arcpy.Delete_management(outputFCPlanform)
    TransferAttributesToLine.main(fcValleyCenterline,
                                  tmpChannelSinuosity,
                                  outputFCPlanform,
                                  workspaceTemp)

    # Calculate planform per segment (planform = channel sinuosity/valley sinuosity)
    fieldPlanform = gis_tools.resetField(outputFCPlanform,"Planform","DOUBLE")
    codeblock = """def calculatePlanform(channel,valley):
        if valley == 0 or valley == -9999:
            return -9999 
        else:
            return channel/valley """
    arcpy.CalculateField_management(outputFCPlanform,
                                    fieldPlanform,
                                    "calculatePlanform(!C_Sin!,!V_Sin!)",
                                    "PYTHON",
                                    codeblock)

    keepFields = [arcpy.Describe(outputFCPlanform).OIDFieldName,
                  arcpy.Describe(outputFCPlanform).shapeFieldName,
                  "Shape_Length",
                  "InputID",
                  "Planform",
                  "C_Sin",
                  "V_Sin"]
    dropFields = [dropField.name for dropField in arcpy.ListFields(outputFCPlanform)]
    arcpy.MakeTableView_management(outputFCPlanform, "fcOutputView")
    for dropField in dropFields:
        if dropField not in keepFields:
            arcpy.DeleteField_management("fcOutputView", dropField)

    # # remove attribute fields if they are found in the input channel sinuosity network
    # attrbFields = ["Planform", "C_Sin", "V_Sin"]
    # checkFields = [f.name for f in arcpy.ListFields(lyrChannelSinuosity)]
    # for attrbField in attrbFields:
    #     if attrbField in checkFields:
    #         arcpy.DeleteField_management(lyrChannelSinuosity, attrbField)
    #
    # # join final valley sinuosity/planform attributes back to input channel sinuosity network
    # arcpy.JoinField_management(lyrChannelSinuosity,
    #                            "InputID",
    #                            "fcOutputView",
    #                            "InputID",
    #                            ["C_Sin", "Planform", "V_Sin"])

    return


def main(source_segments, vb_centerline, outname, temp_workspace=arcpy.env.workspace, xy_dist=160, filterfield="_vb_"):
    """ Calculate channel, planform and valley bottom sinuosity"""

    import gis_tools
    out_segments_file = gis_tools.newGISDataset(arcpy.Describe(outname).path,
                                          arcpy.Describe(outname).basename) if arcpy.Exists(outname) else outname

    arcpy.Copy_management(source_segments, out_segments_file)
    out_segments = gis_tools.newGISDataset("LAYER", "OutputSegments")
    where = '"{}" = 1'.format(filterfield) if filterfield else None
    arcpy.MakeFeatureLayer_management(out_segments_file, out_segments, where_clause=where)
    #fieldname_segments = gis_tools.addUniqueIDField(out_segments, "SegSplitID")

    # Generate points used to find near (split) points.
    arcpy.AddMessage("Generating Near Points for Split")
    endpoints = gis_tools.newGISDataset(temp_workspace, "Endpoints")
    arcpy.FeatureVerticesToPoints_management(out_segments, endpoints, "BOTH_ENDS")
    # todo Maybe not remove triple junctions
    #endpoints_count = gis_tools.newGISDataset(temp_workspace, "Endpoints_Count")
    #arcpy.CollectEvents_stats(endpoints_raw, endpoints_count)
    #endpoints = gis_tools.newGISDataset(temp_workspace, "Endpoints_Final")
    #arcpy.FeatureVerticesToPoints_management(out_segments, endpoints, "DANGLE")
    #lyr_endpoints_count = gis_tools.newGISDataset("LAYER", "EndpointsCount")
    #arcpy.MakeFeatureLayer_management(endpoints_count, lyr_endpoints_count, '''"ICOUNT" > 1''')
    #arcpy.Append_management([lyr_endpoints_count], endpoints, "NO_TEST")
    arcpy.AddXY_management(endpoints)
    arcpy.Near_analysis(endpoints, vb_centerline, location=True, angle=True, method="PLANAR", search_radius=xy_dist)
    sr = arcpy.Describe(endpoints).spatialReference

    with arcpy.da.SearchCursor(endpoints, ["NEAR_X", "NEAR_Y"]) as sc:
        splitpoints = [arcpy.PointGeometry(arcpy.Point(row[0],row[1]), sr) for row in sc if not row[0] == -1]

    split_lines = gis_tools.newGISDataset(temp_workspace, "SplitVB_Centerline")
    arcpy.SplitLineAtPoint_management(vb_centerline, splitpoints, split_lines, search_radius=0.1)

    # Generate Selection Polygons
    arcpy.AddMessage("Generating Selection Polygons")
    lyr_xy_endpoints = gis_tools.newGISDataset("LAYER", "AllEndpoints")
    arcpy.MakeFeatureLayer_management(endpoints, lyr_xy_endpoints, where_clause='''"NEAR_X" <> -1''')
    xy_lines = gis_tools.newGISDataset(temp_workspace, "XYLines")
    arcpy.XYToLine_management(lyr_xy_endpoints, xy_lines, "Point_X", "Point_Y", "NEAR_X", "NEAR_Y", )
    selection_polys = gis_tools.newGISDataset(temp_workspace, "SelectionPolygons")
    arcpy.FeatureToPolygon_management([xy_lines, out_segments, split_lines], selection_polys)

    # Find Lengths and Distances for Segments
    arcpy.AddMessage("Adding Channel Lengths To Segments")
    field_chanlength = gis_tools.resetField(out_segments, "_chanlen_", "DOUBLE")
    arcpy.CalculateField_management(out_segments, field_chanlength, "!shape.length!", "PYTHON_9.3")

    arcpy.AddMessage("Adding Channel Distances and VB Lengths and Distances to Segments")
    lyr_selection_polygons = gis_tools.newGISDataset("LAYER", "SelectionPolygons")
    arcpy.MakeFeatureLayer_management(selection_polys, lyr_selection_polygons)
    lyr_splitlines = gis_tools.newGISDataset("LAYER", "SplitLines")
    arcpy.MakeFeatureLayer_management(split_lines, lyr_splitlines)
    g_mp_vbcenterline = arcpy.Dissolve_management(vb_centerline, out_feature_class=arcpy.Geometry())

    field_vblength = gis_tools.resetField(out_segments, "_vblen_", "DOUBLE")
    field_chandist = gis_tools.resetField(out_segments, "_chandist_", "DOUBLE")
    field_vbdist = gis_tools.resetField(out_segments, "_vbdist_", "DOUBLE")
    field_vbsin = gis_tools.resetField(out_segments, "_sinvb_", "DOUBLE")
    field_chansin = gis_tools.resetField(out_segments, "_sinchan_", "DOUBLE")

    total_segments = int(arcpy.GetCount_management(out_segments).getOutput(0))
    percents = [(total_segments / 10) * value for value in range(1, 10, 1)]
    arcpy.AddMessage("Starting iteration of {} segments".format(total_segments))
    with arcpy.da.UpdateCursor(out_segments, ["SHAPE@", field_vblength, field_chandist, field_vbdist]) as ucSegments:
        i = 1
        percent = 0
        for segment in ucSegments:
            segment_endpoints = [arcpy.PointGeometry(segment[0].firstPoint), arcpy.PointGeometry(segment[0].lastPoint)]
            segment[2] = segment_endpoints[0].distanceTo(segment_endpoints[1])
            valley_endpoints = [g_mp_vbcenterline[0].queryPointAndDistance(segment_endpoints[0])[0],
                                g_mp_vbcenterline[0].queryPointAndDistance(segment_endpoints[1])[0]] # TODO Too Slow?
            segment[3] = valley_endpoints[0].distanceTo(valley_endpoints[1])

            # g_splitlines = arcpy.SplitLineAtPoint_management(g_mp_vbcenterline, valley_endpoints, arcpy.Geometry(), 0.1)
            # g_selection_poly = arcpy.FeatureToPolygon_management([segment[0],
            #                                                       g_mp_vbcenterline[0],
            #                                                       arcpy.Polyline(arcpy.Array([segment[0].firstPoint,
            #                                                                                   valley_endpoints[0].firstPoint])),
            #                                                       arcpy.Polyline(arcpy.Array([segment[0].lastPoint,
            #                                                                                   valley_endpoints[1].firstPoint]))],
            #                                                       arcpy.Geometry())
            # lyr_selection_polygon = gis_tools.newGISDataset("LAYER", "SelectionPolygon")
            # arcpy.MakeFeatureLayer_management(g_selection_poly, lyr_selection_polygon)
            # lyr_g_splitlines = gis_tools.newGISDataset("LAYER", "lyrgsplitlines")
            # arcpy.MakeFeatureLayer_management(g_splitlines, lyr_g_splitlines)
            arcpy.SelectLayerByLocation_management(lyr_selection_polygons, "SHARE_A_LINE_SEGMENT_WITH", segment[0])
            arcpy.SelectLayerByLocation_management(lyr_splitlines, "SHARE_A_LINE_SEGMENT_WITH", lyr_selection_polygons)
            with arcpy.da.SearchCursor(lyr_splitlines, ["SHAPE@LENGTH"]) as scSplitLines:
                segment[1] = sum([line[0] for line in scSplitLines])
            ucSegments.updateRow(segment)
            if i in percents:
                percent = percent + 10
                arcpy.AddMessage("   {}% Complete: Segment {} out of {}".format(percent, i, total_segments))
            i = i+1

    arcpy.AddMessage("Calculating Planform Sinuosity")
    fieldPlanformSinuosity = gis_tools.resetField(out_segments, "_SinPlan_", "DOUBLE")
    codeblock = """def calculatePlanformSinuosity(channel, valley):
        if valley == 0 or valley == -9999:
            return -9999 
        else:
            return channel / valley """
    arcpy.CalculateField_management(out_segments,
                                    fieldPlanformSinuosity,
                                    "calculatePlanformSinuosity(!_chanlen_!, !_vblen_!)",
                                    "PYTHON_9.3",
                                    codeblock)
    arcpy.CalculateField_management(out_segments,
                                    field_chansin,
                                    "calculatePlanformSinuosity(!_chanlen_!, !_chandist_!)",
                                    "PYTHON_9.3",
                                    codeblock)
    arcpy.CalculateField_management(out_segments,
                                    field_vbsin,
                                    "calculatePlanformSinuosity(!_vblen_!, !_vbdist_!)",
                                    "PYTHON_9.3",
                                    codeblock)

    gis_tools.resetField(out_segments, "_QAsin_", "TEXT", TextLength=255)




    return out_segments

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('StreamNetwork', help='Input Segmented Stream Network')
    parser.add_argument('ValleyCenterline', help="Input Valley Centerline", type=str)
    parser.add_argument('OutSinuosity', help="Output Stream Network with Sinuosity")
    parser.add_argument('--fieldFilter', help="(Optional) Field to filter for analysis. Default = None", default=None)
    parser.add_argument('--TempWorkspace', help="(Optional) Specify Temporary Workspace. Default = in_memory workspace)", default="in_memory")
    args = parser.parse_args()

    main(args.StreamNetwork,
         args.ValleyCenterline,
         args.OutSinuosity,
         temp_workspace=args.TempWorkspace,
         )





