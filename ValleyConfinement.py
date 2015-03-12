# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Valley Confinement Tool                                        #
# Purpose:     Calculate Valley Confinement Along a Stream                    #
#                                                                             #
# Author:      Kelly Whitehead                                                #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2014-Nov-01                                                    #
# Version:     0.6          Modified: 2015-Feb-12                             #
# Copyright:   (c) Kelly Whitehead 2014-15                                    #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import sys
import arcpy
import gis_tools

def main(fcCenterline,fcPolygonValleyBottom,fcPolygonChannelRaw,fcConfinementCenterline,fcOutputSegments,scratchWorkspace=arcpy.env.scratchWorkspace,maxXSectionWidth=500.0):

    boolConfinementbySegment = True
    boolChannelIsSegmented = False

    reload(gis_tools)
    arcpy.AddMessage("RiverStyles Confinement Tool")
    arcpy.AddMessage("Saving Centerline Results to: " + fcConfinementCenterline)
    arcpy.AddMessage("Saving Segment Results to: " + fcOutputSegments)
    arcpy.AddMessage("Saving Temporary Files to: " + scratchWorkspace)

    # Create Confined Channel Polygon
    fcConfinedChannel = gis_tools.newGISDataset(scratchWorkspace,"ChannelConfined")
    arcpy.Clip_analysis(fcPolygonChannelRaw,fcPolygonValleyBottom,fcConfinedChannel)

    # Convert Confined Channel polygon to Edges polyline
    fcChannelMargins = gis_tools.newGISDataset(scratchWorkspace,"ChannelMargins")
    arcpy.PolygonToLine_management(fcConfinedChannel,fcChannelMargins)#fcChannelDissolve

    # Copy Line Network for Final Output and Prepare Fields
    if arcpy.Exists(fcOutputSegments):
       arcpy.Delete_management(fcOutputSegments)
    arcpy.CopyFeatures_management(fcCenterline,fcOutputSegments)
    ##Standard Outputs
    arcpy.AddField_management(fcOutputSegments,"Confinement_Summed","DOUBLE")
    arcpy.AddField_management(fcOutputSegments,"Con_Margin_L","DOUBLE")
    arcpy.AddField_management(fcOutputSegments,"Total_Margin_L","DOUBLE")
    arcpy.AddField_management(fcOutputSegments,"Confinement_L","DOUBLE")
    arcpy.AddField_management(fcOutputSegments,"Con_Margin_R","DOUBLE")
    arcpy.AddField_management(fcOutputSegments,"Total_Margin_R","DOUBLE")
    arcpy.AddField_management(fcOutputSegments,"Confinement_R","DOUBLE")
    ##Confinement Centerline Outputs
    arcpy.AddField_management(fcOutputSegments,"Confinement_Centerline","DOUBLE")

    # Create Confinement Edges
    fcConfinementMargins = gis_tools.newGISDataset(scratchWorkspace, "ConfinementMargins")
    arcpy.Intersect_analysis([fcConfinedChannel,fcPolygonValleyBottom],fcConfinementMargins,output_type="LINE")

    # # SEGMENTATION # #
    if boolChannelIsSegmented == False:
        # Merge segments in PolyineCenter to create Route Layer
        tempZFlag = arcpy.env.outputZFlag
        arcpy.env.outputZFlag = "Disabled" # 'empty' z values can cause problem with dissolve
        fcCenterlineDissolved = gis_tools.newGISDataset(scratchWorkspace,"CenterlineDissolved") ### one feature per 'section between trib or branch junctions'
        arcpy.Dissolve_management(fcCenterline,fcCenterlineDissolved,multi_part="SINGLE_PART",unsplit_lines="UNSPLIT_LINES")
        arcpy.env.outputZFlag = tempZFlag

        # Find clip points (ends of segments) along Centerline
        fcCenterlineSegmentPoints = gis_tools.newGISDataset(scratchWorkspace,"CenterlineSegmentPoints")
        fcCenterlineDangles = gis_tools.newGISDataset(scratchWorkspace,"CenterlineDangles")
        fcCenterlineJunctions = gis_tools.newGISDataset(scratchWorkspace,"CenterlineJunctions")
        arcpy.FeatureVerticesToPoints_management(fcCenterline,fcCenterlineSegmentPoints,"END")
        arcpy.FeatureVerticesToPoints_management(fcCenterline,fcCenterlineDangles,"DANGLE")
        arcpy.FeatureVerticesToPoints_management(fcCenterlineDissolved,fcCenterlineJunctions,"BOTH_ENDS")
        lyrCenterlineDangles = gis_tools.newGISDataset('Layer',"lyrCenterlineDangles")
        lyrCenterlineJunctions = gis_tools.newGISDataset('Layer',"lyrCenterlineJunctions")
        arcpy.MakeFeatureLayer_management(fcCenterlineDangles,lyrCenterlineDangles)
        arcpy.MakeFeatureLayer_management(fcCenterlineJunctions,lyrCenterlineJunctions)
        arcpy.SelectLayerByLocation_management(lyrCenterlineJunctions,"INTERSECT",lyrCenterlineDangles,selection_type="NEW_SELECTION")
        arcpy.DeleteFeatures_management(lyrCenterlineJunctions)
        arcpy.SelectLayerByLocation_management(lyrCenterlineDangles,"INTERSECT",fcChannelMargins,selection_type="NEW_SELECTION")
        arcpy.DeleteFeatures_management(lyrCenterlineDangles)
        arcpy.Append_management(fcCenterlineDangles,fcCenterlineSegmentPoints,"NO_TEST")
        lyrCenterlineSegmentPoints = gis_tools.newGISDataset("Layer","lyrCenterlineSegmentPoints")
        arcpy.MakeFeatureLayer_management(fcCenterlineSegmentPoints,lyrCenterlineSegmentPoints)
        arcpy.SelectLayerByLocation_management(lyrCenterlineSegmentPoints,"INTERSECT",lyrCenterlineJunctions,selection_type="NEW_SELECTION")
        arcpy.DeleteFeatures_management(lyrCenterlineSegmentPoints)
        arcpy.AddXY_management(fcCenterlineSegmentPoints)

        # Create Clip lines perpendicular to route layer
        arcpy.AddMessage("Find Perpendicular Angle of Points on Centerline.")
        arcpy.AddField_management(fcCenterlineDissolved,"Route","LONG")
        arcpy.CalculateField_management(fcCenterlineDissolved,"Route","!OBJECTID!","PYTHON")
        fcCenterlineRouted = gis_tools.newGISDataset(scratchWorkspace,"CenterlineRouted")
        arcpy.CreateRoutes_lr(fcCenterlineDissolved,"Route",fcCenterlineRouted,"LENGTH","#","#","UPPER_LEFT","1","0","IGNORE","INDEX")
        tblCenterlineRoutes = gis_tools.newGISDataset(scratchWorkspace,"CenterlineRoutesTable")
        arcpy.LocateFeaturesAlongRoutes_lr(fcCenterlineSegmentPoints,fcCenterlineRouted,"Route","0 Meters",tblCenterlineRoutes,"RID POINT MEAS","FIRST","DISTANCE","ZERO","FIELDS","M_DIRECTON")
        lyrCenterlineEvents = gis_tools.newGISDataset("Layer","lyrCenterlineRouteTable_Events")
        arcpy.MakeRouteEventLayer_lr(fcCenterlineRouted,"Route",tblCenterlineRoutes,"RID POINT MEAS",lyrCenterlineEvents,"#","NO_ERROR_FIELD","ANGLE_FIELD","NORMAL","ANGLE","LEFT","POINT")
        arcpy.AddField_management(lyrCenterlineEvents,"PointID","LONG")
        arcpy.CalculateField_management(lyrCenterlineEvents,"PointID","!OBJECTID!","PYTHON")

        # Extend Valley Width Cross Sections and clip to channel
        arcpy.AddMessage("Extending Valley Width Cross Sections.")
        fcCrossSections = gis_tools.newGISDataset(scratchWorkspace,"CrossSectionsRaw")
        gis_tools.calculatePerpendicularAngles(lyrCenterlineEvents,fcCrossSections,"LOC_ANGLE",float(maxXSectionWidth),"PointID")
        fcCrossSectionsClipped = gis_tools.newGISDataset(scratchWorkspace,"CrossSectionsClipped")
        arcpy.Clip_analysis(fcCrossSections,fcConfinedChannel,fcCrossSectionsClipped) #fcChannelDissolve for fcConfinedChannel

        # Intersect and Split Channel polygon fcchanneledges and PolylineConfinement using cross section lines
        fcIntersectPoints_ChannelMargins = gis_tools.newGISDataset(scratchWorkspace,"IntersectPoints_ChannelMargins")
        fcIntersectPoints_ConfinementMargins = gis_tools.newGISDataset(scratchWorkspace,"IntersectPoints_ConfinementMargins")
        arcpy.Intersect_analysis([fcConfinementMargins,fcCrossSectionsClipped],fcIntersectPoints_ConfinementMargins,output_type="POINT")
        arcpy.Intersect_analysis([fcChannelMargins,fcCrossSectionsClipped],fcIntersectPoints_ChannelMargins,output_type="POINT")
        fcConfinementMargin_Segments = gis_tools.newGISDataset(scratchWorkspace,"ConfinementMargin_Segments")
        fcChannelMargin_Segments = gis_tools.newGISDataset(scratchWorkspace,"ChannelMargin_Segements")
        arcpy.SplitLineAtPoint_management(fcConfinementMargins,fcIntersectPoints_ConfinementMargins,fcConfinementMargin_Segments,search_radius="10 Meters")
        arcpy.SplitLineAtPoint_management(fcChannelMargins,fcIntersectPoints_ChannelMargins,fcChannelMargin_Segments,search_radius="10 Meters")

        #Create Segment Polygons for Selecting edges
        fcChannelSegmentPolygonLines = gis_tools.newGISDataset(scratchWorkspace,"SegmentPolygonLines")
        fcChannelBankLines = gis_tools.newGISDataset(scratchWorkspace,"Bank_Lines")
        fcChannelBankPolygons = gis_tools.newGISDataset(scratchWorkspace,"Bank_Polygons")
        fcChannelSegmentPolygons = gis_tools.newGISDataset(scratchWorkspace,"SegmentPolygons")
        arcpy.Merge_management([fcChannelMargins,fcCrossSectionsClipped],fcChannelSegmentPolygonLines)
        arcpy.FeatureToPolygon_management(fcChannelSegmentPolygonLines,fcChannelSegmentPolygons)
        arcpy.Merge_management([fcChannelSegmentPolygonLines,fcOutputSegments],fcChannelBankLines)
        arcpy.FeatureToPolygon_management(fcChannelBankLines,fcChannelBankPolygons)
        # # End Segmentation# # 
    else:
        pass
    # Create River Side buffer to select right or left banks
    arcpy.AddMessage(" Determining Sides of Bank.")
    fcChannelBankSideBuffer = gis_tools.newGISDataset(scratchWorkspace,"BankSide_Buffer")
    fcChannelBankSidePoints = gis_tools.newGISDataset(scratchWorkspace,"BankSidePoints")
    arcpy.Buffer_analysis(fcOutputSegments,fcChannelBankSideBuffer,"1 Meter","LEFT","FLAT","NONE")
    arcpy.FeatureToPoint_management(fcChannelBankSideBuffer,fcChannelBankSidePoints,"INSIDE")
    arcpy.AddField_management(fcChannelBankPolygons,"BankSide","TEXT","10")
    lyrChannelBanks = gis_tools.newGISDataset("Layer","lyrChannelBanks")
    arcpy.MakeFeatureLayer_management(fcChannelBankPolygons,lyrChannelBanks)
    arcpy.SelectLayerByLocation_management(lyrChannelBanks,"INTERSECT",fcChannelBankSidePoints,selection_type="NEW_SELECTION")
    arcpy.CalculateField_management(lyrChannelBanks,"BankSide","'LEFT'","PYTHON")
    arcpy.SelectLayerByAttribute_management(lyrChannelBanks,"SWITCH_SELECTION")
    arcpy.CalculateField_management(lyrChannelBanks,"BankSide","'RIGHT'","PYTHON")

    # Pepare Layers for Segment Selection
    lyrSegmentPolygons = gis_tools.newGISDataset("Layer","lyrSegmentPolygons")
    lyrConfinementEdgeSegments = gis_tools.newGISDataset("Layer","lyrConfinementEdgeSegments")
    lyrChannelEdgeSegments = gis_tools.newGISDataset("Layer","lyrChannelEdgeSegments")
    arcpy.MakeFeatureLayer_management(fcChannelSegmentPolygons,lyrSegmentPolygons)
    arcpy.MakeFeatureLayer_management(fcConfinementMargin_Segments,lyrConfinementEdgeSegments)
    arcpy.MakeFeatureLayer_management(fcChannelMargin_Segments,lyrChannelEdgeSegments)

    # Perepare Filtered Margins
    fcFilterSplitPoints = gis_tools.newGISDataset(scratchWorkspace,"FilterSplitPoints")
    arcpy.FeatureVerticesToPoints_management(fcConfinementMargin_Segments,fcFilterSplitPoints,"BOTH_ENDS")

    # Prepare Centerline Confinement ##
    fcConfinementMarginSegmentsBankSide = gis_tools.newGISDataset(scratchWorkspace,"ConfinementMarginSegmentsBank")
    lyrConfinementMarginSegmentsBankside = gis_tools.newGISDataset("Layer","lyrConfinementMarginSegmentsBankside")
    arcpy.SpatialJoin_analysis(fcConfinementMargin_Segments,
                               fcChannelBankPolygons,
                               fcConfinementMarginSegmentsBankSide,
                               "JOIN_ONE_TO_ONE",
                               "KEEP_ALL",
                               """BankSide "BankSide" true true false 255 Text 0 0 ,First,#,""" + fcChannelBankPolygons + """,BankSide,-1,-1""")

    arcpy.MakeFeatureLayer_management(fcConfinementMarginSegmentsBankSide,lyrConfinementMarginSegmentsBankside)
    arcpy.SelectLayerByAttribute_management(lyrConfinementMarginSegmentsBankside,"NEW_SELECTION",""" "BankSide" = 'LEFT'""")
    
    fcCenterlineConfinementLeft = transfer_line(lyrConfinementMarginSegmentsBankside,fcCenterlineDissolved,"LEFT")
    arcpy.SelectLayerByAttribute_management(lyrConfinementMarginSegmentsBankside,"NEW_SELECTION",""" "BankSide" = 'RIGHT'""")
    fcCenterlineConfinementRight = transfer_line(lyrConfinementMarginSegmentsBankside,fcCenterlineDissolved,"RIGHT")

    fcConfinementCenterlineIntersected = gis_tools.newGISDataset(scratchWorkspace,"ConfinementCenterlineIntersected")
    arcpy.Intersect_analysis([fcCenterlineConfinementLeft,fcCenterlineConfinementRight],fcConfinementCenterlineIntersected,"ALL")

    #resplit centerline by segments
    arcpy.AddMessage(" Calculating Confinement Along Centerline.")
    if arcpy.Exists(fcConfinementCenterline):
       arcpy.Delete_management(fcConfinementCenterline)# = outputLineFC#gis_tools.newGISDataset(outputLineFC,"ConfinementCenterline")
    arcpy.SplitLineAtPoint_management(fcConfinementCenterlineIntersected,
                                      fcCenterlineSegmentPoints,
                                      fcConfinementCenterline,
                                      "10 Meters")

    #Table and Attributes
    arcpy.AddField_management(fcConfinementCenterline,"Confinement_Type","TEXT",field_length="6")
    arcpy.AddField_management(fcConfinementCenterline,"IsConfined","LONG")

    lyrConfinementCenterline1 = gis_tools.newGISDataset("Layer","lyrConfinementCenterline1")
    arcpy.MakeFeatureLayer_management(fcConfinementCenterline,lyrConfinementCenterline1)
    arcpy.SelectLayerByAttribute_management(lyrConfinementCenterline1,"NEW_SELECTION",""" "Confinement_LEFT" = 1""")
    arcpy.CalculateField_management(lyrConfinementCenterline1,"Confinement_Type","'LEFT'","PYTHON")
    arcpy.SelectLayerByAttribute_management(lyrConfinementCenterline1,"NEW_SELECTION",""" "Confinement_RIGHT" = 1""")
    arcpy.CalculateField_management(lyrConfinementCenterline1,"Confinement_Type","'RIGHT'","PYTHON")
    arcpy.SelectLayerByAttribute_management(lyrConfinementCenterline1,"NEW_SELECTION",""" "Confinement_LEFT" = 1 AND "Confinement_RIGHT" = 1""")
    arcpy.CalculateField_management(lyrConfinementCenterline1,"Confinement_Type","'BOTH'","PYTHON")
    arcpy.SelectLayerByAttribute_management(lyrConfinementCenterline1,"NEW_SELECTION",""" "Confinement_LEFT" = 1 OR "Confinement_RIGHT" = 1""")
    arcpy.CalculateField_management(lyrConfinementCenterline1,"IsConfined","1","PYTHON")
    arcpy.SelectLayerByAttribute_management(lyrConfinementCenterline1,"SWITCH_SELECTION")
    arcpy.CalculateField_management(lyrConfinementCenterline1,"IsConfined","0","PYTHON")
    arcpy.CalculateField_management(lyrConfinementCenterline1,"Confinement_Type","'NONE'","PYTHON")

    # Loop through Segments to Calculate Confinement for Each Segment
    if boolConfinementbySegment == True:
        arcpy.AddMessage(" Calculating Confinement Along Segments.")
        with arcpy.da.UpdateCursor(fcOutputSegments,["OBJECTID", #0
                                                     "Confinement_Summed", #1
                                                     "SHAPE@LENGTH", #2
                                                     "Con_Margin_L", #3
                                                     "Total_Margin_L", #4
                                                     "Confinement_L",#5
                                                     "Con_Margin_R", #6
                                                     "Total_Margin_R", #7
                                                     "Confinement_R", #8
                                                     "Confinement_Centerline" #9
                                                     ]) as ucSegments:
            for segment in ucSegments:
                lyrCurrentSegment = gis_tools.newGISDataset("Layer","lyrCurrentSegment")
                arcpy.MakeFeatureLayer_management(fcOutputSegments,lyrCurrentSegment,'"OBJECTID" = ' + str(segment[0]))

                ## Find Current Segment
                arcpy.SelectLayerByLocation_management(lyrSegmentPolygons,"CONTAINS",lyrCurrentSegment,selection_type="NEW_SELECTION")
                #arcpy.AddMessage(str(arcpy.GetCount_management(lyrSegmentPolygons).getOutput(0)))
                if int(arcpy.GetCount_management(lyrSegmentPolygons).getOutput(0)) == 0:
                    arcpy.SelectLayerByLocation_management(lyrSegmentPolygons,"CROSSED_BY_THE_OUTLINE_OF",lyrCurrentSegment,selection_type="NEW_SELECTION")

                ###use bank polygon for tribs
                #arcpy.SelectLayerByLocation_management(lyrSegmentPolygons,"SHARE_A_LINE_SEGMENT_WITH",lyrCurrentSegment,selection_type="NEW_SELECTION")

                ## Calculate Total Confinement Using both banks (Summed) 
                arcpy.SelectLayerByLocation_management(lyrConfinementEdgeSegments,"SHARE_A_LINE_SEGMENT_WITH",lyrSegmentPolygons,selection_type="NEW_SELECTION")
                arcpy.SelectLayerByLocation_management(lyrChannelEdgeSegments,"SHARE_A_LINE_SEGMENT_WITH",lyrSegmentPolygons,selection_type="NEW_SELECTION")

                dblConfinementEdges = sum([r[0] for r in arcpy.da.SearchCursor(lyrConfinementEdgeSegments,["SHAPE@LENGTH"])])
                dblChannelEdges = sum([r[0] for r in arcpy.da.SearchCursor(lyrChannelEdgeSegments,["SHAPE@LENGTH"])])

                segment[1] = calculate_confinement(dblConfinementEdges,dblChannelEdges)
                arcpy.AddMessage("Segment #" + str(segment[0]) + " | Confinement Summed: " + str(segment[1]))

                ## Calculate Confinement for each bank separately
                #LeftBank
                arcpy.SelectLayerByLocation_management(lyrChannelBanks,"WITHIN",lyrSegmentPolygons,selection_type="NEW_SELECTION")
                arcpy.SelectLayerByLocation_management(lyrChannelBanks,"CONTAINS",fcChannelBankSidePoints,selection_type="SUBSET_SELECTION")
                arcpy.SelectLayerByLocation_management(lyrConfinementEdgeSegments,"SHARE_A_LINE_SEGMENT_WITH",lyrChannelBanks,selection_type="NEW_SELECTION")
                arcpy.SelectLayerByLocation_management(lyrChannelEdgeSegments,"SHARE_A_LINE_SEGMENT_WITH",lyrChannelBanks,selection_type="NEW_SELECTION")
                dblConfinementEdgesL = sum([r[0] for r in arcpy.da.SearchCursor(lyrConfinementEdgeSegments,["SHAPE@LENGTH"])])
                dblChannelEdgesL = sum([r[0] for r in arcpy.da.SearchCursor(lyrChannelEdgeSegments,["SHAPE@LENGTH"])])

                segment[3] = dblConfinementEdgesL
                segment[4] = dblChannelEdgesL
                segment[5] = calculate_confinement(dblConfinementEdgesL,dblChannelEdgesL)

                #RightBank
                arcpy.SelectLayerByLocation_management(lyrChannelBanks,"WITHIN",lyrSegmentPolygons,selection_type="NEW_SELECTION")
                arcpy.SelectLayerByLocation_management(lyrChannelBanks,"CONTAINS",fcChannelBankSidePoints,selection_type="REMOVE_FROM_SELECTION")
                arcpy.SelectLayerByLocation_management(lyrConfinementEdgeSegments,"SHARE_A_LINE_SEGMENT_WITH",lyrChannelBanks,selection_type="NEW_SELECTION")
                arcpy.SelectLayerByLocation_management(lyrChannelEdgeSegments,"SHARE_A_LINE_SEGMENT_WITH",lyrChannelBanks,selection_type="NEW_SELECTION")
                dblConfinementEdgesR = sum([r[0] for r in arcpy.da.SearchCursor(lyrConfinementEdgeSegments,["SHAPE@LENGTH"])])
                dblChannelEdgesR = sum([r[0] for r in arcpy.da.SearchCursor(lyrChannelEdgeSegments,["SHAPE@LENGTH"])])

                segment[6] = dblConfinementEdgesR
                segment[7] = dblChannelEdgesR
                segment[8] = calculate_confinement(dblConfinementEdgesR,dblChannelEdgesR)

                ## Calculate Centerline Confinement
                lyrCenterlineConfinement = gis_tools.newGISDataset("Layer","lyrCenterlineConfinement")
                arcpy.MakeFeatureLayer_management(fcConfinementCenterline,lyrCenterlineConfinement,""" "IsConfined" = 1""")
                arcpy.SelectLayerByLocation_management(lyrCenterlineConfinement,"SHARE_A_LINE_SEGMENT_WITH",lyrCurrentSegment,selection_type="NEW_SELECTION")
                dblConfinementCenterline = sum([r[0] for r in arcpy.da.SearchCursor(lyrCenterlineConfinement,["SHAPE@LENGTH"])])

                segment[9] = calculate_confinement(dblConfinementCenterline,float(segment[2]))

                ## Update Row
                ucSegments.updateRow(segment)

        arcpy.AddMessage("Confinement Calculations Complete.")

    return

def calculate_confinement(dblConfinedMarginLength,dblTotalLength):

    if dblTotalLength == 0: ##Avoid Division by Zero. Report -9999 if segment has strange geometry.
        dblConfinement = -9999
    else:
        dblConfinement = (dblConfinedMarginLength / dblTotalLength)

    return dblConfinement

def transfer_line(fcInLine,fcToLine,strStreamSide):
    outputWorkspace = arcpy.Describe(fcInLine).path
    fcOutput = gis_tools.newGISDataset(outputWorkspace,"CenterlineConfinement" + strStreamSide)
    
    # Split Centerline by Line Ends 
    fcSplitPoints = gis_tools.newGISDataset(outputWorkspace,"SplitPoints_Confinement" + strStreamSide)
    arcpy.FeatureVerticesToPoints_management(fcInLine,fcSplitPoints,"BOTH_ENDS")
    tblNearPointsConfinement = gis_tools.newGISDataset(outputWorkspace,"NearPointsConfinement" + strStreamSide)
    arcpy.GenerateNearTable_analysis(fcSplitPoints,fcToLine,tblNearPointsConfinement,location="LOCATION",angle="ANGLE")
    lyrNearPointsConfinement = gis_tools.newGISDataset("Layer","lyrNearPointsConfinement"+ strStreamSide)
    arcpy.MakeXYEventLayer_management(tblNearPointsConfinement,"NEAR_X","NEAR_Y",lyrNearPointsConfinement,fcToLine)
    arcpy.SplitLineAtPoint_management(fcToLine,lyrNearPointsConfinement,fcOutput,search_radius="10 Meters")
    
    # Prepare Fields
    strConfinementField = "Confinement_" + strStreamSide
    arcpy.AddField_management(fcOutput,strConfinementField,"LONG")

    # Transfer Attributes by Centroids
    fcCentroidPoints = gis_tools.newGISDataset(outputWorkspace,"CentroidPoints_Confinement" + strStreamSide)
    arcpy.FeatureVerticesToPoints_management(fcInLine,fcCentroidPoints,"MID")
    tblNearPointsCentroid = gis_tools.newGISDataset(outputWorkspace,"NearPointsCentroid" + strStreamSide)
    arcpy.GenerateNearTable_analysis(fcCentroidPoints,fcToLine,tblNearPointsCentroid,location="LOCATION",angle="ANGLE")
    lyrNearPointsCentroid = gis_tools.newGISDataset("Layer","lyrNearPointsCentroid" + strStreamSide)
    arcpy.MakeXYEventLayer_management(tblNearPointsCentroid,"NEAR_X","NEAR_Y",lyrNearPointsCentroid,fcToLine)
    lyrToLineSegments = gis_tools.newGISDataset("Layer","lyrToLineSegments")
    arcpy.MakeFeatureLayer_management(fcOutput,lyrToLineSegments)
    
    arcpy.SelectLayerByLocation_management(lyrToLineSegments,"INTERSECT",lyrNearPointsCentroid,"0.01 Meter","NEW_SELECTION")
    arcpy.CalculateField_management(lyrToLineSegments,strConfinementField,1,"PYTHON")
    
    return fcOutput

if __name__ == "__main__":
    
    main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6])