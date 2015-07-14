# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Moving Window Analysis for Line Network                        #
# Purpose:     Run a generic moving window analysis for a variable along a    #
#              line network.                                                  #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-May-05                                                    # 
# Version:     1.2                                                            #
# Modified:    2015-May-05                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import os
import sys
import arcpy
import gis_tools

# # Main Function # # 
def main(
    fcLineNetwork,
    fieldStreamRouteID,
    fieldAttribute,
    strSeedDistance,
    inputliststrWindowSize,
    boolOverlap=False,
    outputWorkspace=arcpy.env.scratchWorkspace):
    """Perform a Moving Window Analysis on a Line Network."""

    liststrWindowSize = inputliststrWindowSize.split(";")

    fcLineNetworkDissolved = gis_tools.newGISDataset(outputWorkspace,"GNAT_MWA_LineNetworkDissolved")
    arcpy.Dissolve_management(fcLineNetwork,fcLineNetworkDissolved,fieldStreamRouteID,multi_part=False,unsplit_lines=True)

    listLineGeometries = arcpy.CopyFeatures_management(fcLineNetworkDissolved,arcpy.Geometry())
    listWindows = []
    listSeeds = []
    listWindowEvents = []
    listgWindows = []
    intSeedID = 0
    
    iRoutes = int(arcpy.GetCount_management(fcLineNetworkDissolved).getOutput(0))
    arcpy.SetProgressor("step","Processing Each Route",0,iRoutes,1)
    iRoute = 0
    with arcpy.da.SearchCursor(fcLineNetworkDissolved,["SHAPE@",fieldStreamRouteID,"SHAPE@LENGTH"]) as scLines:
        for fLine in scLines: #Loop Through Routes
            arcpy.SetProgressorLabel("Route: " + str(iRoute) + " Seed Point: " + str(intSeedID))
            arcpy.SetProgressorPosition(iRoute)
            gLine = fLine[0]
            dblSeedPointPosition = float(max(liststrWindowSize))/2 #Start Seeds at position of largest window
            while dblSeedPointPosition + float(max(liststrWindowSize))/2 < fLine[2]:
                arcpy.SetProgressorLabel("Route: " + str(iRoute) + " Seed Point: " + str(intSeedID))
                gSeedPointPosition = gLine.positionAlongLine(dblSeedPointPosition)
                listSeeds.append([scLines[1],intSeedID,gSeedPointPosition])#gSeedPointPosition.X,gSeedPointPosition.Y])
                for strWindowSize in liststrWindowSize:
                    dblWindowSize = float(strWindowSize)
                    dblLengthStart = dblSeedPointPosition - dblWindowSize/2
                    dblLengthEnd = dblSeedPointPosition + dblWindowSize/2
                    
                    gPointStartLocation = gLine.positionAlongLine(dblLengthStart)
                    gPointEndLocation = gLine.positionAlongLine(dblLengthEnd)
                    gTemp = arcpy.Geometry()
                    listgWindowTemp = arcpy.SplitLineAtPoint_management(gLine,[gPointStartLocation,gPointEndLocation],gTemp,"1 METER")
                    for gWindowTemp in listgWindowTemp:
                        if abs(gWindowTemp.length - dblWindowSize) < 10 :
                            listgWindows.append([scLines[1],intSeedID,dblWindowSize,gWindowTemp])

                    listWindows.append([scLines[1],intSeedID,dblWindowSize,gPointStartLocation])
                    listWindows.append([scLines[1],intSeedID,dblWindowSize,gPointEndLocation])
                    listWindowEvents.append([scLines[1],intSeedID,dblWindowSize,dblLengthStart,dblLengthEnd])
                dblSeedPointPosition = dblSeedPointPosition + float(strSeedDistance)
                intSeedID = intSeedID + 1
            iRoute = iRoute + 1

    fcSeedPoints = gis_tools.newGISDataset(outputWorkspace,"GNAT_MWA_SeedPoints")
    fcWindowEndPoints = gis_tools.newGISDataset(outputWorkspace,"GNAT_MWA_WindowEndPoints")
    fcWindowLines = gis_tools.newGISDataset(outputWorkspace,"GNAT_MWA_WindowLines")
      
    arcpy.CreateFeatureclass_management(outputWorkspace,"GNAT_MWA_SeedPoints","POINT",spatial_reference=fcLineNetwork)
    arcpy.CreateFeatureclass_management(outputWorkspace,"GNAT_MWA_WindowEndPoints","POINT",spatial_reference=fcLineNetwork)
    arcpy.CreateFeatureclass_management(outputWorkspace,"GNAT_MWA_WindowLines","POLYLINE",spatial_reference=fcLineNetwork)

    gis_tools.resetField(fcSeedPoints,"RouteID","LONG")
    gis_tools.resetField(fcSeedPoints,"SeedPointID","LONG")
    
    gis_tools.resetField(fcWindowEndPoints,"RouteID","LONG")
    gis_tools.resetField(fcWindowEndPoints,"SeedPointID","LONG")
    gis_tools.resetField(fcWindowEndPoints,"WindowSize","DOUBLE")

    gis_tools.resetField(fcWindowLines,"RouteID","LONG")
    gis_tools.resetField(fcWindowLines,"SeedPointID","LONG")
    gis_tools.resetField(fcWindowLines,"WindowSize","DOUBLE")

    with arcpy.da.InsertCursor(fcSeedPoints,["RouteID","SeedPointID","SHAPE@XY"]) as icSeedPoints:
        for row in listSeeds:
            icSeedPoints.insertRow(row)

    with arcpy.da.InsertCursor(fcWindowEndPoints,["RouteID","SeedPointID","WindowSize","SHAPE@XY"]) as icWindowEndPoints:
        for row in listWindows:
            icWindowEndPoints.insertRow(row)

    with arcpy.da.InsertCursor(fcWindowLines,["RouteID","SeedPointID","WindowSize","SHAPE@"]) as icWindowLines:
        for row in listgWindows:
            icWindowLines.insertRow(row)

    fcIntersected = gis_tools.newGISDataset(outputWorkspace,"GNAT_MWA_IntersectWindowAttributes")
    arcpy.Intersect_analysis([fcWindowLines,fcLineNetwork],fcIntersected,"ALL",output_type="LINE")

    tblSummaryStatistics = gis_tools.newGISDataset(outputWorkspace,"GNAT_MWA_SummaryStatsTable")
    arcpy.Statistics_analysis(fcIntersected,tblSummaryStatistics,"Shape_Length SUM",fieldStreamRouteID + ";SeedPointID;WindowSize;" + fieldAttribute)

    tblSummaryStatisticsPivot = gis_tools.newGISDataset(outputWorkspace,"GNAT_MWA_SummaryStatisticsPivotTable")
    arcpy.PivotTable_management(tblSummaryStatistics,"Route;SeedPointID;WindowSize",fieldAttribute,"SUM_Shape_Length",tblSummaryStatisticsPivot)
    
    gis_tools.resetField(tblSummaryStatisticsPivot,"Confinement","DOUBLE")
    arcpy.CalculateField_management(tblSummaryStatisticsPivot,"Confinement","!IsConfined1!/(!IsConfined0! + !IsConfined1!)","PYTHON")

    #Pivot Confinement on WindowSize
    tblSummaryStatisticsWindowPivot = gis_tools.newGISDataset(outputWorkspace,"GNAT_MWA_SummaryStatisticsWindowPivotTable")
    arcpy.PivotTable_management(tblSummaryStatisticsPivot,fieldStreamRouteID + ";SeedPointID","WindowSize","Confinement",tblSummaryStatisticsWindowPivot)
    
    strWindowSizeFields = ""
    for WindowSize in liststrWindowSize:
        strWindowSizeFields = strWindowSizeFields + ";WindowSize" + WindowSize
    strWindowSizeFields = strWindowSizeFields.lstrip(";")

    #Join Above table to seed points
    arcpy.JoinField_management(fcSeedPoints,"SeedPointID",tblSummaryStatisticsWindowPivot,"SeedPointID",strWindowSizeFields)

    return

if __name__ == "__main__":

    main(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4],
        sys.argv[5],
        sys.argv[6],
        sys.argv[7],
        sys.argv[8])