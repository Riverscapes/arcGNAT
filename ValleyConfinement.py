# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Valley Confinement Tool                                        #
# Purpose:     Calculate Valley Confinement Along a Stream Network            #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2014-Nov-01                                                    #
# Version:     1.1                                                            #
# Modified:    2015-Apr-23                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2014-15                                    #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import sys
import arcpy
import gis_tools
import DividePolygonBySegment

# # Main Function # #
def main(fcInputStreamLineNetwork,
         fcInputValleyBottomPolygon,
         fcInputChannelPolygon,
         fcOutputRawConfiningState,
         fcOutputConfinementSegments,
         fcOutputConfiningMargins,
         scratchWorkspace):

    ## Reload modules and Prepare processing environments
    reload(gis_tools)
    arcpy.AddMessage("GNAT Confinement Tool")

    # Create Confined Channel Polygon
    fcConfinedChannel = gis_tools.newGISDataset(scratchWorkspace,"ChannelConfined")
    arcpy.Clip_analysis(fcInputChannelPolygon,fcInputValleyBottomPolygon,fcConfinedChannel)

    # Convert Confined Channel polygon to Edges polyline
    fcChannelMargins = gis_tools.newGISDataset(scratchWorkspace,"ChannelMargins")
    arcpy.PolygonToLine_management(fcConfinedChannel,fcChannelMargins)

    # Create Confinement Edges
    if fcOutputConfiningMargins:
        gis_tools.resetData(fcOutputConfiningMargins)
        fcConfiningMargins = fcOutputConfiningMargins
    else:
        fcConfiningMargins = gis_tools.newGISDataset(scratchWorkspace, "ConfiningMargins")
    arcpy.Intersect_analysis([fcConfinedChannel,fcInputValleyBottomPolygon],fcConfiningMargins,output_type="LINE")
    
    # Merge segments in PolyineCenter to create Route Layer
    tempZFlag = arcpy.env.outputZFlag
    arcpy.env.outputZFlag = "Disabled" # 'empty' z values can cause problem with dissolve
    fcStreamNetworkDissolved = gis_tools.newGISDataset(scratchWorkspace,"StreamNetworkDissolved") ### one feature per 'section between trib or branch junctions'
    arcpy.Dissolve_management(fcInputStreamLineNetwork,fcStreamNetworkDissolved,multi_part="SINGLE_PART",unsplit_lines="UNSPLIT_LINES")
    arcpy.env.outputZFlag = tempZFlag

    fcNetworkSegmentPoints = gis_tools.newGISDataset(scratchWorkspace,"StreamNetworkSegmentPoints")
    arcpy.FeatureVerticesToPoints_management(fcInputStreamLineNetwork,fcNetworkSegmentPoints,"END")
    fcStreamNetworkDangles = gis_tools.newGISDataset(scratchWorkspace,"StreamNetworkDangles")
    arcpy.FeatureVerticesToPoints_management(fcInputStreamLineNetwork,fcStreamNetworkDangles,"DANGLE")

    #SegmentPolgyons
    arcpy.AddMessage("GNAT CON: Preparing Segmented Polygons")
    fcChannelBankLines = gis_tools.newGISDataset(scratchWorkspace,"Bank_Lines")
    fcChannelBankPolygons = gis_tools.newGISDataset(scratchWorkspace,"Bank_Polygons")
    fcChannelSegmentPolygons = gis_tools.newGISDataset(scratchWorkspace,"SegmentPolygons")
    fcChannelSegmentPolygonLines = gis_tools.newGISDataset(scratchWorkspace,"SegmentPolygonLines")
    fcChannelBankNearLines = gis_tools.newGISDataset(scratchWorkspace,"Bank_NearLines")
    DividePolygonBySegment.main(fcInputStreamLineNetwork,fcConfinedChannel,fcChannelSegmentPolygons)
    #arcpy.Copy_management(fcConfinedChannel,fcChannelSegmentPolygons)
    arcpy.PolygonToLine_management(fcChannelSegmentPolygons,fcChannelSegmentPolygonLines)
    lyrStreamNetworkDangles = gis_tools.newGISDataset("LAYER", "lyrStreamNetworkDangles")
    arcpy.MakeFeatureLayer_management(fcStreamNetworkDangles,lyrStreamNetworkDangles)
    arcpy.SelectLayerByLocation_management(lyrStreamNetworkDangles,"INTERSECT",fcConfinedChannel)
    arcpy.Near_analysis(lyrStreamNetworkDangles,fcChannelSegmentPolygonLines,location="LOCATION")
    arcpy.AddXY_management(lyrStreamNetworkDangles)
    arcpy.XYToLine_management(lyrStreamNetworkDangles,
                                fcChannelBankNearLines,
                                "POINT_X",
                                "POINT_Y",
                                "NEAR_X",
                                "NEAR_Y")

    arcpy.Merge_management([fcChannelSegmentPolygonLines,fcInputStreamLineNetwork,fcChannelBankNearLines],fcChannelBankLines)
    arcpy.FeatureToPolygon_management(fcChannelBankLines,fcChannelBankPolygons)
        
    # Intersect and Split Channel polygon fcchanneledges and PolylineConfinement using cross section lines
    arcpy.AddMessage("GNAT CON: Intersect and Split Channel Polygons")
    fcIntersectPoints_ChannelMargins = gis_tools.newGISDataset(scratchWorkspace,"IntersectPoints_ChannelMargins")
    fcIntersectPoints_ConfinementMargins = gis_tools.newGISDataset(scratchWorkspace,"IntersectPoints_ConfinementMargins")
    arcpy.Intersect_analysis([fcConfiningMargins,fcChannelSegmentPolygonLines],fcIntersectPoints_ConfinementMargins,output_type="POINT")
    arcpy.Intersect_analysis([fcChannelMargins,fcChannelSegmentPolygonLines],fcIntersectPoints_ChannelMargins,output_type="POINT")
    fcConfinementMargin_Segments = gis_tools.newGISDataset(scratchWorkspace,"ConfinementMargin_Segments")
    fcChannelMargin_Segments = gis_tools.newGISDataset(scratchWorkspace,"ChannelMargin_Segements")
    arcpy.SplitLineAtPoint_management(fcConfiningMargins,fcIntersectPoints_ConfinementMargins,fcConfinementMargin_Segments,search_radius="10 Meters")
    arcpy.SplitLineAtPoint_management(fcChannelMargins,fcIntersectPoints_ChannelMargins,fcChannelMargin_Segments,search_radius="10 Meters")

    # Create River Side buffer to select right or left banks
    arcpy.AddMessage("GNAT CON: Determining Sides of Bank.")
    fcChannelBankSideBuffer = gis_tools.newGISDataset(scratchWorkspace,"BankSide_Buffer")
    fcChannelBankSidePoints = gis_tools.newGISDataset(scratchWorkspace,"BankSidePoints")
    arcpy.Buffer_analysis(fcInputStreamLineNetwork,fcChannelBankSideBuffer,"1 Meter","LEFT","FLAT","NONE")
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

    # Prepare Continuous Confinement ##
    arcpy.AddMessage("GNAT CON: Determining Continuous Confinement along Stream Network.")
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
    
    fcStreamNetworkConfinementLeft = transfer_line(lyrConfinementMarginSegmentsBankside,fcStreamNetworkDissolved,"LEFT")
    arcpy.SelectLayerByAttribute_management(lyrConfinementMarginSegmentsBankside,"NEW_SELECTION",""" "BankSide" = 'RIGHT'""")
    fcStreamNetworkConfinementRight = transfer_line(lyrConfinementMarginSegmentsBankside,fcStreamNetworkDissolved,"RIGHT")

    fcConfinementStreamNetworkIntersected = gis_tools.newGISDataset(scratchWorkspace,"ConfinementStreamNetworkIntersected")
    arcpy.Intersect_analysis([fcStreamNetworkConfinementLeft,fcStreamNetworkConfinementRight],fcConfinementStreamNetworkIntersected,"ALL")

    #resplit centerline by segments
    arcpy.AddMessage("GNAT CON: Calculating Confinement For Stream Network Segments.")
    if arcpy.Exists(fcOutputRawConfiningState):
       arcpy.Delete_management(fcOutputRawConfiningState)# = outputLineFC#gis_tools.newGISDataset(outputLineFC,"ConfinementCenterline")
    arcpy.SplitLineAtPoint_management(fcConfinementStreamNetworkIntersected,
                                      fcNetworkSegmentPoints,
                                      fcOutputRawConfiningState,
                                      "10 Meters")

    #Table and Attributes
    arcpy.AddField_management(fcOutputRawConfiningState,"Confinement_Type","TEXT",field_length="6")
    arcpy.AddField_management(fcOutputRawConfiningState,"IsConfined","LONG")

    lyrConfinementStreamNetwork1 = gis_tools.newGISDataset("Layer","lyrStreamNetworkCenterline1")
    arcpy.MakeFeatureLayer_management(fcOutputRawConfiningState,lyrConfinementStreamNetwork1)
    arcpy.SelectLayerByAttribute_management(lyrConfinementStreamNetwork1,"NEW_SELECTION",""" "Confinement_LEFT" = 1""")
    arcpy.CalculateField_management(lyrConfinementStreamNetwork1,"Confinement_Type","'LEFT'","PYTHON")
    arcpy.SelectLayerByAttribute_management(lyrConfinementStreamNetwork1,"NEW_SELECTION",""" "Confinement_RIGHT" = 1""")
    arcpy.CalculateField_management(lyrConfinementStreamNetwork1,"Confinement_Type","'RIGHT'","PYTHON")
    arcpy.SelectLayerByAttribute_management(lyrConfinementStreamNetwork1,"NEW_SELECTION",""" "Confinement_LEFT" = 1 AND "Confinement_RIGHT" = 1""")
    arcpy.CalculateField_management(lyrConfinementStreamNetwork1,"Confinement_Type","'BOTH'","PYTHON")
    arcpy.SelectLayerByAttribute_management(lyrConfinementStreamNetwork1,"NEW_SELECTION",""" "Confinement_LEFT" = 1 OR "Confinement_RIGHT" = 1""")
    arcpy.CalculateField_management(lyrConfinementStreamNetwork1,"IsConfined","1","PYTHON")
    arcpy.SelectLayerByAttribute_management(lyrConfinementStreamNetwork1,"SWITCH_SELECTION")
    arcpy.CalculateField_management(lyrConfinementStreamNetwork1,"IsConfined","0","PYTHON")
    arcpy.CalculateField_management(lyrConfinementStreamNetwork1,"Confinement_Type","'NONE'","PYTHON")

    # Loop through Segments to Calculate Confinement for Each Segment
    if fcOutputConfinementSegments:

        # Copy Line Network for Final Output and Prepare Fields
        if arcpy.Exists(fcOutputConfinementSegments):
           arcpy.Delete_management(fcOutputConfinementSegments)
        arcpy.CopyFeatures_management(fcInputStreamLineNetwork,fcOutputConfinementSegments)
        ##Confinement By Margins Outputs
        arcpy.AddField_management(fcOutputConfinementSegments,"Confinement_Margin_Summed","DOUBLE")
        arcpy.AddField_management(fcOutputConfinementSegments,"Length_ConfinedMargin_Left","DOUBLE")
        arcpy.AddField_management(fcOutputConfinementSegments,"Length_ChannelMargin_Left","DOUBLE")
        arcpy.AddField_management(fcOutputConfinementSegments,"Confinement_Margin_Left","DOUBLE")
        arcpy.AddField_management(fcOutputConfinementSegments,"Length_ConfinedMargin_Right","DOUBLE")
        arcpy.AddField_management(fcOutputConfinementSegments,"Length_ChannelMargin_Right","DOUBLE")
        arcpy.AddField_management(fcOutputConfinementSegments,"Confinement_Margin_Right","DOUBLE")
        ##Confinement By LineNetwork Outputs
        arcpy.AddField_management(fcOutputConfinementSegments,"Confinement_LineNetwork_All","DOUBLE")
        arcpy.AddField_management(fcOutputConfinementSegments,"Confinement_LineNetwork_Both","DOUBLE")
        arcpy.AddField_management(fcOutputConfinementSegments,"Confinement_LineNetwork_Left","DOUBLE")
        arcpy.AddField_management(fcOutputConfinementSegments,"Confinement_LineNetwork_Right","DOUBLE")


        arcpy.AddMessage("GNAT CON: Calculating Confinement Along Segments.")
        desc_fcOutputSegments = arcpy.Describe(fcOutputConfinementSegments)
        with arcpy.da.UpdateCursor(fcOutputConfinementSegments,[str(desc_fcOutputSegments.OIDFieldName), #0
                                                     "Confinement_Margin_Summed", #1
                                                     "SHAPE@LENGTH", #2
                                                     "Length_ConfinedMargin_Left", #3
                                                     "Length_ChannelMargin_Left", #4
                                                     "Confinement_Margin_Left",#5
                                                     "Length_ConfinedMargin_Right", #6
                                                     "Length_ChannelMargin_Right", #7
                                                     "Confinement_Margin_Right", #8
                                                     "Confinement_LineNetwork_All", #9
                                                     "Confinement_LineNetwork_Both", #10
                                                     "Confinement_LineNetwork_Left", #11
                                                     "Confinement_LineNetwork_Right" #12
                                                     ]) as ucSegments:
            for segment in ucSegments:
                lyrCurrentSegment = gis_tools.newGISDataset("Layer","lyrCurrentSegment")
                arcpy.MakeFeatureLayer_management(fcOutputConfinementSegments,lyrCurrentSegment,'"' + str(desc_fcOutputSegments.OIDFieldName)+ '" = ' + str(segment[0]))

                ## Find Current Segment
                arcpy.SelectLayerByLocation_management(lyrSegmentPolygons,"CONTAINS",lyrCurrentSegment,selection_type="NEW_SELECTION")
                #arcpy.AddMessage(str(arcpy.GetCount_management(lyrSegmentPolygons).getOutput(0)))
                if int(arcpy.GetCount_management(lyrSegmentPolygons).getOutput(0)) == 0:
                    arcpy.SelectLayerByLocation_management(lyrSegmentPolygons,"CROSSED_BY_THE_OUTLINE_OF",lyrCurrentSegment,selection_type="NEW_SELECTION")

                ## Calculate Total Confinement Using both banks (Summed) 
                arcpy.SelectLayerByLocation_management(lyrConfinementEdgeSegments,"SHARE_A_LINE_SEGMENT_WITH",lyrSegmentPolygons,selection_type="NEW_SELECTION")
                arcpy.SelectLayerByLocation_management(lyrChannelEdgeSegments,"SHARE_A_LINE_SEGMENT_WITH",lyrSegmentPolygons,selection_type="NEW_SELECTION")

                dblConfinementEdges = sum([r[0] for r in arcpy.da.SearchCursor(lyrConfinementEdgeSegments,["SHAPE@LENGTH"])])
                dblChannelEdges = sum([r[0] for r in arcpy.da.SearchCursor(lyrChannelEdgeSegments,["SHAPE@LENGTH"])])

                segment[1] = calculate_confinement(dblConfinementEdges,dblChannelEdges)
                arcpy.AddMessage("Segment #" + str(segment[0]) + " | Confinement Margins Summed: " + str(segment[1]))

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

                ## Calculate Confinement from continuous stream network
                # Is Confined
                lyrLineNetworkConfinement = gis_tools.newGISDataset("Layer","lyrLineNetworkConfinement")
                arcpy.MakeFeatureLayer_management(fcOutputRawConfiningState,lyrLineNetworkConfinement,""" "IsConfined" = 1""")
                arcpy.SelectLayerByLocation_management(lyrLineNetworkConfinement,"SHARE_A_LINE_SEGMENT_WITH",lyrCurrentSegment,selection_type="NEW_SELECTION")
                dblConfinementLineNetwork = sum([r[0] for r in arcpy.da.SearchCursor(lyrLineNetworkConfinement,["SHAPE@LENGTH"])])
                segment[9] = calculate_confinement(dblConfinementLineNetwork,float(segment[2]))

                # Both
                lyrLineNetworkConfinementBoth = gis_tools.newGISDataset("Layer","lyrLineNetworkConfinementBoth")
                arcpy.MakeFeatureLayer_management(fcOutputRawConfiningState,lyrLineNetworkConfinementBoth,""" "Confinement_Type" = 'BOTH'""")
                arcpy.SelectLayerByLocation_management(lyrLineNetworkConfinementBoth,"SHARE_A_LINE_SEGMENT_WITH",lyrCurrentSegment,selection_type="NEW_SELECTION")
                dblConfinementLineNetworkBoth = sum([r[0] for r in arcpy.da.SearchCursor(lyrLineNetworkConfinementBoth,["SHAPE@LENGTH"])])
                segment[10] = calculate_confinement(dblConfinementLineNetworkBoth,float(segment[2]))
                # Left
                lyrLineNetworkConfinementLeft = gis_tools.newGISDataset("Layer","lyrLineNetworkConfinementLeft")
                arcpy.MakeFeatureLayer_management(fcOutputRawConfiningState,lyrLineNetworkConfinementLeft,""" "Confinement_Type" = 'LEFT'""")
                arcpy.SelectLayerByLocation_management(lyrLineNetworkConfinementLeft,"SHARE_A_LINE_SEGMENT_WITH",lyrCurrentSegment,selection_type="NEW_SELECTION")
                dblConfinementLineNetworkLeft = sum([r[0] for r in arcpy.da.SearchCursor(lyrLineNetworkConfinementLeft,["SHAPE@LENGTH"])])
                segment[11] = calculate_confinement(dblConfinementLineNetworkLeft,float(segment[2]))
                # Right
                lyrLineNetworkConfinementRight = gis_tools.newGISDataset("Layer","lyrLineNetworkConfinementRight")
                arcpy.MakeFeatureLayer_management(fcOutputRawConfiningState,lyrLineNetworkConfinementRight,""" "Confinement_Type" = 'RIGHT'""")
                arcpy.SelectLayerByLocation_management(lyrLineNetworkConfinementRight,"SHARE_A_LINE_SEGMENT_WITH",lyrCurrentSegment,selection_type="NEW_SELECTION")
                dblConfinementLineNetworkRight = sum([r[0] for r in arcpy.da.SearchCursor(lyrLineNetworkConfinementRight,["SHAPE@LENGTH"])])
                segment[12] = calculate_confinement(dblConfinementLineNetworkRight,float(segment[2]))

                ## Update Row
                ucSegments.updateRow(segment)

        arcpy.AddMessage("GNAT CON: Confinement Calculations Complete.")

    return

def calculate_confinement(dblConfinedMarginLength,dblTotalLength):

    if dblTotalLength == 0: ##Avoid Division by Zero. Report -9999 if segment has strange geometry.
        dblConfinement = -9999
    else:
        dblConfinement = (dblConfinedMarginLength / dblTotalLength)

    return dblConfinement

def transfer_line(fcInLine,fcToLine,strStreamSide):
    outputWorkspace = arcpy.Describe(fcInLine).path
    fcOutput = gis_tools.newGISDataset(outputWorkspace,"LineNetworkConfinement" + strStreamSide)
    
    # Split Line Network by Line Ends 
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
    
    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3],
         sys.argv[4],
         sys.argv[5],
         sys.argv[6],
         sys.argv[7],
         sys.argv[8],
         sys.argv[9])