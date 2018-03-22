# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Calculate Braidedness                                          #
# Purpose:     This tool calculated the braidedness of a stream channel.      #
#              The braidedness metric is calculated per stream segment.       #
#                                                                             #
# Author:      Jesse Langdon (jesse@southforkresearch.org)                    #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2018-March-22                                                  #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

import arcpy
import gis_tools


# finds a specific field in a feature class
def findField(inputFC, field):
  fieldLineOID = [f.name for f in arcpy.ListFields(inputFC)]
  if field in fieldLineOID:
      return True


# set up field mappings for merged node feature class
def nodeFieldMap(fcList):
    fm = arcpy.FieldMappings()
    for fc in fcList:
        fm.addTable(fc)
    # remove output fields from field mappings, except NODE_TYPE
    for f in fm.fields:
        if f.name != "NODE_TYPE":
            fm.removeFieldMap(fm.findFieldMapIndex(f.name))
    return fm


# main processing function
def main(fcInputSegments,
         fcInputAttrbNetwork,
         tempWorkspace):

    arcpy.env.overwriteOutput = True

    # Turn off Z and M geometry
    arcpy.env.outputMFlag = "Disabled"
    arcpy.env.outputZFlag = "Disabled"

    # Prep temporary files and layers
    arcpy.MakeFeatureLayer_management(fcInputSegments, "lyrInputSegments")
    arcpy.MakeFeatureLayer_management(fcInputAttrbNetwork, "lyrInputAttrbNetwork")
    fcInputAttrbNetworkTemp = gis_tools.newGISDataset(tempWorkspace, "fcInputAttrbNetworkTemp")
    arcpy.CopyFeatures_management("lyrInputAttrbNetwork", fcInputAttrbNetworkTemp)
    fcBraidDslv = gis_tools.newGISDataset(tempWorkspace, "fcBraidDslv")
    fcSegmentDslv = gis_tools.newGISDataset(tempWorkspace, "fcSegmentDslv")
    fcNodeBraidToBraid = gis_tools.newGISDataset(tempWorkspace, "fcNodeBraidToBraid")
    fcNodeBraidToBraidSingle = gis_tools.newGISDataset(tempWorkspace, "fcNodeBraidToBraidSingle")
    fcNodeBraidToBraidDslv = gis_tools.newGISDataset(tempWorkspace, "fcNodeBraidToBraidDslv")
    fcNodeBraidToMainstem = gis_tools.newGISDataset(tempWorkspace, "fcNodeBraidToMainstem")
    fcNodeBraidToMainstemSingle = gis_tools.newGISDataset(tempWorkspace, "fcNodeBraidToMainstemSingle")
    fcNodeBraidToMainstemDslv = gis_tools.newGISDataset(tempWorkspace, "fcNodeBraidToMainstemDslv")
    fcNodeTribConfluence = gis_tools.newGISDataset(tempWorkspace, "fcNodeTribConfluence")
    fcNodeTribConfluenceSingle = gis_tools.newGISDataset(tempWorkspace, "fcNodeTribConfuenceSingle")
    fcNodeTribConfluenceDslv = gis_tools.newGISDataset(tempWorkspace, "fcNodeTribConfluenceDslv")
    fcNodesAll = gis_tools.newGISDataset(tempWorkspace, "fcNodesAll")
    fcNodesToSegments = gis_tools.newGISDataset(tempWorkspace, "fcNodesToSegments")
    tblNodeBMSummary = gis_tools.newGISDataset(tempWorkspace, "tblNodeBMSummary")
    tblNodeTCSummary = gis_tools.newGISDataset(tempWorkspace, "tblNodeTCSummary")

    # Check if the segmented stream network has a field named LineOID
    if findField(fcInputSegments, "SegmentID"):
        LineOID = "SegmentID"
        pass
    else:
        arcpy.AddMessage("SegmentID attribute field not found in input stream feature class. Using ObjectID field...")
        LineOID = arcpy.Describe(fcInputSegments).OIDFieldName

    # Check if the attributed network as been run through the Generate Network Attributes tool.
    if findField(fcInputAttrbNetworkTemp, "_edgetype_"):
        pass
    else:
        arcpy.AddError("The attributed network input is missing the '_edgetype_' field. Please run the "
                       "network through the Generate Network Attributes tool before running this tool.")

    # Braid-to-braid nodes
    arcpy.AddMessage("GNAT CTT: Generating braid-to-braid nodes...")
    arcpy.MakeFeatureLayer_management(fcInputAttrbNetworkTemp, "lyrInputAttrbNetworkTemp")
    arcpy.SelectLayerByAttribute_management("lyrInputAttrbNetworkTemp","NEW_SELECTION", """ "_edgetype_" = 'braid' """)
    #arcpy.SelectLayerByLocation_management("lyrInputAttrbNetworkTemp", "HAVE_THEIR_CENTER_IN",
    #                                       "lyrInputSegments", "#", "REMOVE_FROM_SELECTION")
    arcpy.Dissolve_management("lyrInputAttrbNetworkTemp", fcBraidDslv, "#", "#", "SINGLE_PART")
    arcpy.Intersect_analysis([fcBraidDslv], fcNodeBraidToBraid, "ONLY_FID", "#", "POINT")
    arcpy.MakeFeatureLayer_management(fcNodeBraidToBraid, "lyrNodeBraidToBraid")
    arcpy.MultipartToSinglepart_management("lyrNodeBraidToBraid", fcNodeBraidToBraidSingle)
    arcpy.MakeFeatureLayer_management(fcNodeBraidToBraidSingle, "lyrNodeBraidToBraidSingle")
    arcpy.Dissolve_management("lyrNodeBraidToBraidSingle", fcNodeBraidToBraidDslv, "#", "#", "SINGLE_PART")
    arcpy.MakeFeatureLayer_management(fcNodeBraidToBraidDslv, "lyrNodeBraidToBraidDslv")
    arcpy.AddField_management("lyrNodeBraidToBraidDslv", "NODE_TYPE", "TEXT")
    arcpy.CalculateField_management("lyrNodeBraidToBraidDslv", "NODE_TYPE", '"BB"', "PYTHON_9.3")
    # Braid-to-mainstem nodes
    arcpy.AddMessage("GNAT CTT: Generating braid-to-mainstem nodes...")
    arcpy.Intersect_analysis([fcBraidDslv,fcInputSegments],fcNodeBraidToMainstem, "#", "#", "POINT")
    arcpy.MakeFeatureLayer_management(fcNodeBraidToMainstem, "lyrNodeBraidToMainstem")
    arcpy.MultipartToSinglepart_management("lyrNodeBraidToMainstem", fcNodeBraidToMainstemSingle)
    arcpy.MakeFeatureLayer_management(fcNodeBraidToMainstemSingle, "lyrNodeBraidToMainstemSingle")
    arcpy.Dissolve_management("lyrNodeBraidToMainstemSingle", fcNodeBraidToMainstemDslv, "#", "#", "SINGLE_PART")
    arcpy.MakeFeatureLayer_management(fcNodeBraidToMainstemDslv, "lyrNodeBraidToMainstemDslv")
    arcpy.AddField_management("lyrNodeBraidToMainstemDslv", "NODE_TYPE", "TEXT")
    arcpy.CalculateField_management("lyrNodeBraidToMainstemDslv", "NODE_TYPE", '"BM"', "PYTHON_9.3")
    # Tributary confluence nodes
    arcpy.AddMessage("GNAT CTT: Generating tributary nodes...")
    arcpy.Dissolve_management("lyrInputSegments", fcSegmentDslv, "#", "#", "SINGLE_PART")
    arcpy.Intersect_analysis([fcSegmentDslv], fcNodeTribConfluence, "ONLY_FID", "#", "POINT")
    arcpy.MakeFeatureLayer_management(fcNodeTribConfluence, "lyrNodeTribConfluence")
    arcpy.MultipartToSinglepart_management("lyrNodeTribConfluence", fcNodeTribConfluenceSingle)
    arcpy.MakeFeatureLayer_management(fcNodeTribConfluenceSingle, "lyrNodeTribConfluenceSingle")
    arcpy.Dissolve_management("lyrNodeTribConfluenceSingle", fcNodeTribConfluenceDslv, "#", "#", "SINGLE_PART")
    arcpy.MakeFeatureLayer_management(fcNodeTribConfluenceDslv, "lyrNodeTribConfluenceDslv")
    arcpy.AddField_management("lyrNodeTribConfluenceDslv", "NODE_TYPE", "TEXT")
    arcpy.CalculateField_management("lyrNodeTribConfluenceDslv", "NODE_TYPE", '"TC"', "PYTHON_9.3")
    # Merge nodes feature classes together
    arcpy.AddMessage("GNAT CTT: Merge and save node feature class...")
    node_list = ["lyrNodeBraidToBraidDslv", "lyrNodeBraidToMainstemDslv", "lyrNodeTribConfluenceDslv"]
    fieldMapping = nodeFieldMap(node_list)
    arcpy.Merge_management(node_list, fcNodesAll, fieldMapping)
    arcpy.MakeFeatureLayer_management(fcNodesAll, "lyrNodesAll")
    # Spatial join nodes to segmented stream network
    arcpy.SpatialJoin_analysis("lyrInputSegments", "lyrNodesAll", fcNodesToSegments, "JOIN_ONE_TO_MANY",
                               "KEEP_COMMON", "#", "INTERSECT")
    # Summarize each node type by attribute field LineOID
    arcpy.AddMessage("GNAT CTT: Summarize nodes per stream segments...")
    arcpy.MakeFeatureLayer_management(fcNodesToSegments, "lyrNodesToSegments")
    arcpy.SelectLayerByAttribute_management("lyrNodesToSegments", "NEW_SELECTION", """"NODE_TYPE" = 'BM'""")
    arcpy.Statistics_analysis("lyrNodesToSegments", tblNodeBMSummary, [["NODE_TYPE", "COUNT"]], LineOID)
    arcpy.SelectLayerByAttribute_management("lyrNodesToSegments", "CLEAR_SELECTION")
    arcpy.SelectLayerByAttribute_management("lyrNodesToSegments", "NEW_SELECTION", """"NODE_TYPE" = 'TC'""")
    arcpy.Statistics_analysis("lyrNodesToSegments", tblNodeTCSummary, [["NODE_TYPE", "COUNT"]], LineOID)
    arcpy.SelectLayerByAttribute_management("lyrNodesToSegments", "CLEAR_SELECTION")
    # Spatial join each summary table as a new field to final segment network
    arcpy.AddField_management("lyrInputSegments", "NODES_BM", "TEXT")
    arcpy.AddField_management("lyrInputSegments", "NODES_TC", "TEXT")
    arcpy.MakeTableView_management(tblNodeBMSummary, "viewNodeBMSummary")
    arcpy.MakeTableView_management(tblNodeTCSummary, "viewNodeTCSummary")
    arcpy.AddJoin_management("lyrInputSegments", LineOID, "viewNodeBMSummary", LineOID, "KEEP_COMMON")
    arcpy.CalculateField_management("lyrInputSegments", "NODES_BM", '"!COUNT_NODE_TYPE!"', "PYTHON_9.3")
    arcpy.RemoveJoin_management("lyrInputSegments")
    arcpy.AddJoin_management("lyrInputSegments", LineOID, "viewNodeTCSummary", LineOID, "KEEP_COMMON")
    arcpy.CalculateField_management("lyrInputSegments", "NODES_TC", '"!COUNT_NODE_TYPE!"', "PYTHON_9.3")
    arcpy.RemoveJoin_management("lyrInputSegments")

    arcpy.AddMessage("GNAT CTT: Processing complete.")
