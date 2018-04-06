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
# Modified:    2018-Mar-22                                                    #
#                                                                             #
# Copyright:   (c) South Fork Research, Inc. 2017                             #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

import arcpy
from lib import gis_tools
from collections import defaultdict

__version__ = "2.0.01"


def main(source_segments,
         vb_centerline,
         temp_workspace,
         xy_dist=150,
         filterfield="_vb_",
         field_segid="SegmentID",
         out_shapefile=None):
    """ Calculate channel, planform and valley bottom sinuosity"""

    if out_shapefile:
        arcpy.CopyFeatures_management(source_segments, out_shapefile)
        source_segments = out_shapefile
    out_segments = gis_tools.newGISDataset("LAYER", "OutputSegments")

    where = '"{}" = 1'.format(filterfield) if filterfield in arcpy.ListFields(source_segments) else None  # TODO Test
    arcpy.MakeFeatureLayer_management(source_segments, out_segments, where_clause=where)

    # Generate Split Points
    arcpy.AddMessage("Generating Near Points for Split")
    endpoints = gis_tools.newGISDataset(temp_workspace, "Endpoints")
    arcpy.FeatureVerticesToPoints_management(out_segments, endpoints, "BOTH_ENDS")
    arcpy.AddXY_management(endpoints)
    arcpy.Near_analysis(endpoints, vb_centerline, location=True, angle=True, method="PLANAR", search_radius=xy_dist)
    sr = arcpy.Describe(endpoints).spatialReference

    ddict_vb_points = defaultdict(list)
    with arcpy.da.SearchCursor(endpoints, ["NEAR_X", "NEAR_Y", field_segid]) as sc:
        splitpoints = [arcpy.PointGeometry(arcpy.Point(row[0], row[1]), sr) for row in sc if not row[0] == -1]
        sc.reset()
        for row in sc:
            if row[0] != -1:
                ddict_vb_points[row[2]].append(arcpy.Point(row[0], row[1]))

    # Generate Valley Bottom distances
    arcpy.AddMessage("Generating VB Centerline Segment Distances")
    dict_vb_lines = {}
    for segid, lpts in ddict_vb_points.iteritems():
        line = arcpy.Polyline(arcpy.Array(lpts))
        dict_vb_lines[segid] = line
    vb_lines = gis_tools.newGISDataset("in_memory", "VBDIST")
    arcpy.CopyFeatures_management([line for line in dict_vb_lines.itervalues()], vb_lines)

    split_lines = gis_tools.newGISDataset(temp_workspace, "SplitVB_Centerline")
    arcpy.SplitLineAtPoint_management(vb_centerline, splitpoints, split_lines, search_radius=0.1)

    # Selection Polygons from VB_Dist
    arcpy.AddMessage("Generating VB Selection Polygons")
    vb_polys = gis_tools.newGISDataset(temp_workspace, "VB_Polygons")
    arcpy.FeatureToPolygon_management([vb_centerline, vb_lines], vb_polys)  # TODO test use vb_centerlines for faster procesing?

    dict_vb_dist = {}
    lyr_selection_polygons = gis_tools.newGISDataset("LAYER", "SelectionPolygons")
    arcpy.MakeFeatureLayer_management(vb_polys, lyr_selection_polygons)
    lyr_splitlines = gis_tools.newGISDataset("LAYER", "SplitLines")
    arcpy.MakeFeatureLayer_management(split_lines, lyr_splitlines)
    for segid, vbline in dict_vb_lines.iteritems():
        arcpy.SelectLayerByLocation_management(lyr_selection_polygons, "SHARE_A_LINE_SEGMENT_WITH", vbline)
        arcpy.SelectLayerByLocation_management(lyr_splitlines, "SHARE_A_LINE_SEGMENT_WITH", lyr_selection_polygons)
        with arcpy.da.SearchCursor(lyr_splitlines, ["SHAPE@LENGTH"]) as scSplitLines:
            dict_vb_dist[segid] = sum([line[0] for line in scSplitLines])

    # Find Lengths and Distances for Segments
    arcpy.AddMessage("Adding Channel Lengths To Segments")
    field_chanlength = gis_tools.resetField(out_segments, "Chan_Len", "DOUBLE")
    arcpy.CalculateField_management(out_segments, field_chanlength, "!shape.length!", "PYTHON_9.3")

    # Channel Segment Distances
    arcpy.AddMessage("Adding Channel Distances and VB Lengths and Distances to Segments")
    field_vblength = gis_tools.resetField(out_segments, "VB_Len", "DOUBLE")
    field_chandist = gis_tools.resetField(out_segments, "Chan_Dist", "DOUBLE")
    field_vbdist = gis_tools.resetField(out_segments, "VB_Dist", "DOUBLE")

    total_segments = int(arcpy.GetCount_management(out_segments).getOutput(0))
    percents = [(total_segments / 10) * value for value in range(1, 10, 1)]
    arcpy.AddMessage("Starting iteration of {} segments".format(total_segments))
    with arcpy.da.UpdateCursor(out_segments, ["SHAPE@", field_vblength, field_chandist, field_vbdist, field_segid]) as ucSegments:
        i = 1
        percent = 0
        for segment in ucSegments:
            segment_endpoints = [arcpy.PointGeometry(segment[0].firstPoint), arcpy.PointGeometry(segment[0].lastPoint)]
            segment[2] = segment_endpoints[0].distanceTo(segment_endpoints[1])
            segment[3] = dict_vb_lines[segment[4]].length if dict_vb_lines.has_key(segment[4]) else 0.0
            segment[1] = dict_vb_dist[segment[4]] if dict_vb_dist.has_key(segment[4]) else 0.0
            ucSegments.updateRow(segment)
            if i in percents:
                percent = percent + 10
                arcpy.AddMessage("   {}% Complete: Segment {} out of {}".format(percent, i, total_segments))
            i = i+1
        arcpy.AddMessage("  100% Complete: Segment {} out of {}".format(total_segments, total_segments))

    # Calculate Sinuosty Metrics
    arcpy.AddMessage("Calculating Sinuosity Values")
    fieldPlanformSinuosity = gis_tools.resetField(out_segments, "Sin_Plan", "DOUBLE")
    field_vbsin = gis_tools.resetField(out_segments, "Sin_VB", "DOUBLE")
    field_chansin = gis_tools.resetField(out_segments, "Sin_Chan", "DOUBLE")

    codeblock = """def calculate_sinuosity(seg_length, seg_distance):
        if seg_distance == 0 or seg_distance == -9999:
            return -9999 
        else:
            return seg_length / seg_distance """

    arcpy.CalculateField_management(out_segments,
                                    fieldPlanformSinuosity,
                                    "calculate_sinuosity(!{}!, !{}!)".format(field_chanlength, field_vblength),
                                    "PYTHON_9.3",
                                    codeblock)
    arcpy.CalculateField_management(out_segments,
                                    field_chansin,
                                    "calculate_sinuosity(!{}!, !{}!)".format(field_chanlength, field_chandist),
                                    "PYTHON_9.3",
                                    codeblock)
    arcpy.CalculateField_management(out_segments,
                                    field_vbsin,
                                    "calculate_sinuosity(!{}!, !{}!)".format(field_vblength, field_vbdist),
                                    "PYTHON_9.3",
                                    codeblock)

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

    # main(args.StreamNetwork,
    #      args.ValleyCenterline,
    #      args.OutSinuosity,
    #      temp_workspace=args.TempWorkspace)
