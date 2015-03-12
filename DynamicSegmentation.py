# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Network Segmentation                                           #
# Purpose:                                                                    #
#                                                                             #
# Author:      Kelly Whitehead                                                #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2014-Oct-17                                                    #
# Version:     0.1          Modified:                                         #
# Copyright:   (c) Kelly Whitehead 2014                                       #                                                
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python


# # Import Modules # #
import os
import sys
import math
import arcpy
from gis_tools import *

outputPath = "C:\\GIS\\StreamNetwork"
outputName = "OutputGeodatabase01.gdb"
outputWorkspace = outputPath + "\\" + outputName + "\\"

fcValleyEdges = outputWorkspace + "ValleyEdges"
rastfileWidth = outputWorkspace + "ValleyWidth"
tblValleyBins = outputWorkspace + "ValleyBins"
rastfileReclassWidth = outputWorkspace + "ValleyWidthBins"
fcValleyWidth = outputWorkspace + "ValleyWidthPoly"
fcWidthChangeRaw = outputWorkspace + " WidthChangeRaw"
fcWidthChange = outputWorkspace + "WidthChange"
fcCenterlinePrep = outputWorkspace + "CenterlinePrep"
fcCenterlineRoute = outputWorkspace + "CenterlineRoutes"
tblCenterlineRoute = outputWorkspace + "CenterlineRouteTable"
lyrCenterlineEvents = "Layer_CenterlineRouteTable_Events"
fcWidthCrossLines = outputWorkspace + "WidthCrossSections"

maxValleyWidth = 3000

def main(fcInputLineNetwork,fcValleyCenterline,fcValleyPolygon,DEM,strValleyBinType,dblValleyBinValue,slopeThreshold,valleywidthThreshold):

    # Workspace Prep
    arcpy.AddMessage(outputWorkspace.rstrip("\\"))
    if arcpy.Exists(outputWorkspace.rstrip("\\")):
        pass
    else:
        arcpy.CreateFileGDB_management(outputPath,outputName)
    fcLineNetwork = outputWorkspace + "Network"
    resetData(fcLineNetwork)
    arcpy.CopyFeatures_management(fcInputLineNetwork,fcLineNetwork)

    ### Valley Width Segmentation ###

    # Convert Valley Polygon to edges
    arcpy.AddMessage("Convert Valley Polygon to edges...")
    resetData(fcValleyEdges)
    arcpy.PolygonToLine_management(fcValleyPolygon,fcValleyEdges)
    
    # Generate Euclidean Distance Raster
    arcpy.AddMessage("Generate Euclidean Distance Raster...")
    resetData(rastfileWidth)
    arcpy.env.extent = DEM
    arcpy.env.snapRaster = DEM
    arcpy.env.cellSize = DEM
    arcpy.env.mask = fcValleyPolygon
    arcpy.AddMessage("  Run sa.EucDistance")
    rasterDistance = arcpy.sa.EucDistance(fcValleyEdges)
    arcpy.AddMessage("  Run sa.Times")
    rasterWidth = arcpy.sa.Times(rasterDistance,2)
    arcpy.AddMessage("  Save Raster.")
    rasterWidth.save(rastfileWidth)

    # Set up Valley Width Bin Criteria
    arcpy.AddMessage("Set up Valley Width Bin Criteria...")
    resetData(tblValleyBins)
    arcpy.CreateTable_management(outputWorkspace, "ValleyBins")
    arcpy.AddField_management(tblValleyBins,"FromValue","DOUBLE")
    arcpy.AddField_management(tblValleyBins,"ToValue","DOUBLE")
    arcpy.AddField_management(tblValleyBins,"Bin","SHORT")


    if strValleyBinType == "EqualInterval":
        listBins = range(int(rasterWidth.minimum),int(rasterWidth.maximum),int(dblValleyBinValue))
        valueStartBin = int(rasterWidth.minimum)
    #TODO: add other types of bins
    #elif strValleyBinType == ""    
    #listBins = range(0100100010>0)

    with arcpy.da.InsertCursor(tblValleyBins,["FromValue","ToValue","Bin"]) as icValleyBins:
        valueLowerBin = valueStartBin
        intBinReclass = 1
        for bin in listBins:
            icValleyBins.insertRow([valueLowerBin,bin,intBinReclass])
            valueLowerBin = bin
            intBinReclass = intBinReclass + 1

    # Reclass Valley Width Raster by Bins
    arcpy.AddMessage("Reclass Valley Width Raster by Bins...")
    resetData(rastfileReclassWidth)
    #resetData(rasterWidthClass)
    rasterWidthClass = arcpy.sa.ReclassByTable(rasterWidth,tblValleyBins,"FromValue","ToValue","Bin")
    rasterWidthClass.save(rastfileReclassWidth)

    # Convert Reclassed Distance to Polygons
    arcpy.AddMessage("Convert Reclassed Distance to Polygons...")
    resetData(fcValleyWidth)
    arcpy.RasterToPolygon_conversion(rasterWidthClass,fcValleyWidth,"SIMPLIFY")
    #TODO: Clean up any polygon holes due to rasterization

    # Intersect Distance Bands with Centerline
    arcpy.AddMessage("Intersect Distance Bands with Centerline...")
    resetData(fcWidthChange)
    arcpy.Intersect_analysis([fcValleyCenterline,fcValleyWidth],fcWidthChange,output_type="POINT")
    arcpy.DeleteIdentical_management(fcWidthChange,["Shape"])
    
    # Find Perpendicular Angle of Points on Centerline
    arcpy.AddMessage("Find Perpendicular Angle of Points on Centerline...")
    resetData(fcCenterlinePrep)
    arcpy.AddField_management(fcCenterlinePrep,"Route","SHORT")
    arcpy.CalculateField_management(fcCenterlinePrep,"Route","!OBJECTID!","PYTHON")

    resetData(fcCenterlineRoute)
    arcpy.CreateRoutes_lr(fcCenterlinePrep,"Route",fcCenterlineRoute,"LENGTH","#","#","UPPER_LEFT","1","0","IGNORE","INDEX")

    resetData(tblCenterlineRoute)
    arcpy.LocateFeaturesAlongRoutes_lr(fcWidthChange,fcCenterlineRoute,"Route","0 Meters",tblCenterlineRoute,"RID POINT MEAS","FIRST","DISTANCE","ZERO","FIELDS","M_DIRECTON")

    resetData(lyrCenterlineEvents)
    arcpy.MakeRouteEventLayer_lr(fcCenterlineRoute,"Route",tblCenterlineRoute,"RID POINT MEAS",lyrCenterlineEvents,"#","NO_ERROR_FIELD","ANGLE_FIELD","NORMAL","ANGLE","LEFT","POINT")

    arcpy.AddField_management(lyrCenterlineEvents,"PointID","SHORT")
    arcpy.CalculateField_management(lyrCenterlineEvents,"PointID","!OBJECTID!","PYTHON")

    # Extend Valley Width Cross Sections
    arcpy.AddMessage("Extend Valley Width Cross Sections...")
    resetData(fcWidthCrossLines)
    calculatePerpendicularAngles(lyrCenterlinesEvents,fcWidthCrossLines,"Angle_Loc",maxValleyWidth,"PointID")

    # Slice Valley Polygon and Attribute with Binned Width
    arcpy.AddMessage("")

    # Slice Network and Attribute with Binned Width
    arcpy.AddMessage("")


    return

# # Run as Script # # 
if __name__ == "__main__":
    inputPolylineFC = sys.argv[1] # Str Feature class path
    inputValleyPolygon = sys.argv[2] # Int
    inputValleyCenterline = sys.argv[3]
    inputDEM = sys.argv[4] # Str Raster DataLayer
    minSegmentLength = sys.argv[5]# Dbl
    maxSegmentsPerReach = sys.argv[6]# Int
    slopeThreshold = sys.argv[7]# max difference between candidate reaches to become a subreach
    valleywidthThreshold = sys.argv[8]# max difference between candidate reaches to become a subreach

    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3],
         sys.argv[4],
         sys.argv[5],
         sys.argv[6],
         sys.argv[7],
         sys.argv[8])