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


def main(fcChannelSinuosity,
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


def split_line_near(source_segments, to_split, outname, temp_workspace=arcpy.env.workspace):
    """ Geoprocccsing: split features in a line network by features in an adjacent line network"""

    import gis_tools
    temp_source_segments = gis_tools.newGISDataset(temp_workspace, "SourceSegments")
    arcpy.Copy_management(source_segments, temp_source_segments)
    fieldname_segments = gis_tools.addUniqueIDField(temp_source_segments, "SegSplitID")

    # Generate points used to find near (split) points.
    endpoints_raw = gis_tools.newGISDataset(temp_workspace, "Endpoints_raw")
    endpoints_count = gis_tools.newGISDataset(temp_workspace, "Endpoints_Count")
    endpoints = gis_tools.newGISDataset(temp_workspace, "Endpoints_Final")
    arcpy.FeatureVerticesToPoints_management(temp_source_segments, endpoints_raw, "BOTH_ENDS")
    arcpy.CollectEvents_stats(endpoints_raw, endpoints_count)
    lyr_endpoints_count = gis_tools.newGISDataset("LAYER", "EndpointsCount")
    arcpy.FeatureVerticesToPoints_management(temp_source_segments, endpoints, "DANGLE")
    arcpy.MakeFeatureLayer_management(endpoints_count, lyr_endpoints_count, '''"ICOUNT" > 1''')
    arcpy.Append_management([lyr_endpoints_count], endpoints, "NO_TEST")

    arcpy.Near_analysis(endpoints, to_split, location=True, angle=True, method="PLANAR")
    sr = arcpy.Describe(endpoints).spatialReference
    with arcpy.da.SearchCursor(endpoints, ["NEAR_X", "NEAR_Y"]) as sc:
        splitpoints = [arcpy.PointGeometry(arcpy.Point(row[0],row[1]), sr) for row in sc]

    split_lines = gis_tools.newGISDataset(arcpy.Describe(outname).path,
                                          arcpy.Describe(outname).name) if arcpy.Exists(outname) else outname
    arcpy.SplitLineAtPoint_management(to_split, splitpoints, split_lines, search_radius=0.1)

    lyr_all_endpoints = gis_tools.newGISDataset('LAYER', "AllEndpoints")
    arcpy.MakeFeatureLayer_management(endpoints_raw, lyr_all_endpoints)

    vb_endpoints = gis_tools.newGISDataset(temp_workspace, "vb_endpoints")
    arcpy.FeatureVerticesToPoints_management(split_lines, vb_endpoints, "BOTH_ENDS")

    vb_endpoints_join = gis_tools.newGISDataset(temp_workspace, "vb_endpoints_join")
    arcpy.SpatialJoin_analysis(vb_endpoints, lyr_all_endpoints, match_option="CLOSEST", out_feature_class=vb_endpoints_join)



    vb_distance = gis_tools.newGISDataset(temp_workspace, "vb_distance")
    arcpy.PointsToLine_management(vb_endpoints_join, vb_distance, "ORIG_FID")


    # include: nearest to endpoints + vb_endpoints

    return split_lines



def associate_line_segments(dest_lines, source_lines, search_dist=None, temp_workspace=arcpy.env.workspace):

    # Generate Join ID's?

    centroids = gis_tools.newGISDataset(temp_workspace, "DestNetworkCentroids")
    arcpy.FeatureVerticesToPoints_management(dest_lines, centroids, "MID")

    centroids_join = gis_tools.newGISDataset(temp_workspace, "DestNetworkCentroids_Join")
    arcpy.SpatialJoin_analysis(centroids, source_lines, "JOIN_ONE_TO_ONE", "KEEP_ALL",
                               match_option="CLOSEST",
                               out_feature_class=centroids_join)





# straightline distances for
# vb
# segments

# seglengths
# vb lengths