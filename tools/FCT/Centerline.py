'''
Created on 21 fev. 2013
Last update on 07 fev. 2014

Update on 2015-Apr-09 by Kelly Whitehead (kelly@southforkresearch.org) to fix issues with tool not generating the centerline in all sections of the valley bottom, and generating extra segments in other locations.

@author: Clement Roux

@contact: clement.roux@ens-lyon.fr
          CNRS - UMR5600 Environnement Ville Societe
          15 Parvis Ren?escartes, BP 7000, 69342 Lyon Cedex 07, France
         
@note: For each use of the FluvialCorridor toolbox leading to a publication, report, presentation or any other
       document, please refer the following article :
       Roux, C., Alber, A., Bertrand, M., Vaudor, L., Piegay, H., submitted. "FluvialCorridor": A new ArcGIS 
       package for multiscale riverscape exploration. Geomorphology
       
@summary: Centerline is an open-source python and arcPy code.
          This script has been implemented to extract the centerline line of "long" polygon features (i.e. with
          one larger dimension compared to the other). It is based on a Thiessen polygonization of the input
          polygon boundaries. 
          
'''

# Import of required libraries
import arcpy
import os
from tools.FCT import def__SLEM as dS, def__UpToDateShapeLengthField as UPD_SL
from lib import ClearInMemory


# Polygon = r"C:\JL\Testing\GNAT\Issue9\shp\Entiat_ValleyBottom.shp"
# Polyline = r"C:\JL\Testing\GNAT\Issue9\shp\Entiat_EP.shp"
# DisaggregationStep = 10
# Smoothing = 10
# Output = r"C:\JL\Testing\GNAT\Issue9\shp\Entiat_ValleyCenterline.shp"

def main(Polygon,Polyline,DisaggregationStep,Smoothing,Output):
    # Allow the temporary outputs overwrite
    arcpy.env.overwriteOutput = True

    # Derived variable from inputs
    name = os.path.split(os.path.splitext(Polygon)[0])[1]

    # Number of steps
    nstep = 12
    ncurrentstep=1


    #===============================================================================
    # CODING
    #===============================================================================
    #/creation of the extreme points
    arcpy.AddMessage("Looking for the extreme points of the input polyline - Step "  + str(ncurrentstep) + "/" + str(nstep))

    ExtremePoints = arcpy.FeatureVerticesToPoints_management(Polyline, "in_memory\\ExtremePoints", "DANGLE") ### Simplified the method for finding Extreme Points to use line "dangles". This appears to have removed a bunch of extra extreme points found in the temp data.
    ### KMW: Removed this section, I do not fully understand how this functions, but it does not appear to break the process.
    # arcpy.AddXY_management(ExtremePoints) 
    # arcpy.AddField_management(ExtremePoints, "Del", "SHORT")
    # ExtPts.ExtremePoints(ExtremePoints)
    #
    # Make = arcpy.MakeFeatureLayer_management(ExtremePoints, "in_memory\\Make")
    # Selection = arcpy.SelectLayerByAttribute_management(Make, "NEW_SELECTION", "\"Del\" = 1")
    #
    # arcpy.DeleteFeatures_management(Selection)
    ###

    #/splitting of the polygon with extreme points
    ncurrentstep+=1
    arcpy.AddMessage("Converting the input polygon to line - Step " + str(ncurrentstep) + "/" + str(nstep))
    PolyToLine = arcpy.FeatureToLine_management(Polygon, "in_memory\\PolyToLine", "", "ATTRIBUTES")

    ncurrentstep+=1
    arcpy.AddMessage("Looking for the longer distance between extreme points and the polygon - Step " + str(ncurrentstep) + "/" + str(nstep))
    NearTable = arcpy.GenerateNearTable_analysis(ExtremePoints, PolyToLine, "in_memory\\NearTable", "", "LOCATION", "NO_ANGLE")
    NearPoints = arcpy.MakeXYEventLayer_management(NearTable, "NEAR_X", "NEAR_Y", "NearPoints", ExtremePoints)
    arcpy.CopyFeatures_management("NearPoints","in_memory\\NearPoints")
    ### Removed this Section. It appears to find the max distance in the table, for use in splitting the lines?
    #rows = arcpy.SearchCursor(NearTable)
    # Counter = 0
    # for row in rows :
    #     if row.NEAR_DIST > Counter :
    #         Counter = row.NEAR_DIST
    # Counter+=1
    ###

    ncurrentstep+=1
    arcpy.AddMessage("Splitting polygon with the extreme points - Step " + str(ncurrentstep) + "/" + str(nstep))
    FracTEMP = arcpy.SplitLineAtPoint_management(PolyToLine, "NearPoints", "in_memory\\FracTEMP", "0.1 METERS")### Changed to use near points for splitting, also added "0.1 METERS" search distance to solve an esri bug in this function.

    ncurrentstep+=1
    arcpy.AddMessage("Deleting residual segments - Step " + str(ncurrentstep) + "/" + str(nstep))
    FracTEMPToPoints = arcpy.FeatureVerticesToPoints_management(FracTEMP, "in_memory\\FracTEMPToPoints", "BOTH_ENDS")

    arcpy.AddField_management(FracTEMP, "Fusion", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    fieldnames = [f.name for f in arcpy.ListFields(FracTEMP)]
    arcpy.CalculateField_management(FracTEMP, "Fusion", "["+fieldnames[0]+"]", "VB", "")

    SpatialRef = arcpy.Describe(Polygon).spatialReference
    XY = arcpy.MakeXYEventLayer_management(NearTable, "NEAR_X", "NEAR_Y", "in_memory\\XY", SpatialRef, "")

    NearTable2 = arcpy.GenerateNearTable_analysis(XY, FracTEMPToPoints, "in_memory\\NearTable2", "", "LOCATION", "NO_ANGLE", "ALL", "2")
    fieldnames = [f.name for f in arcpy.ListFields(FracTEMP)]
    arcpy.JoinField_management(FracTEMPToPoints, fieldnames[0], NearTable2, "NEAR_FID", ["NEAR_FID"])

    MakeFracTEMPToPoints = arcpy.MakeFeatureLayer_management(FracTEMPToPoints, "in_memory\\MakeFracTEMPToPoints", "", "", "ORIG_FID ORIG_FID VISIBLE NONE")
    MakeFracTEMP = arcpy.MakeFeatureLayer_management(FracTEMP, "in_memory\\MakeFracTEMP", "", "", "ORIG_FID ORIG_FID VISIBLE NONE") 

    SelectionPoints = arcpy.SelectLayerByAttribute_management(MakeFracTEMPToPoints, "NEW_SELECTION", "\"NEAR_FID\" IS NULL")
    SelectLine = arcpy.SelectLayerByLocation_management(MakeFracTEMP, "BOUNDARY_TOUCHES", SelectionPoints, "", "NEW_SELECTION")
    arcpy.CalculateField_management(SelectLine, "Fusion", "10000", "VB", "")

    FracPoly_TEMP = arcpy.Dissolve_management(FracTEMP, "in_memory\\FracPoly_TEMP", "Fusion", "", "MULTI_PART", "DISSOLVE_LINES")

    FracPoly = arcpy.MultipartToSinglepart_management(FracPoly_TEMP, "in_memory\\FracPoly")
    arcpy.DeleteField_management(FracPoly, "Fusion")

    ncurrentstep+=1
    arcpy.AddMessage("Split the input polygon - Step " + str(ncurrentstep) + "/" + str(nstep))
    PolySplitTEMP = dS.SLEM(FracPoly, DisaggregationStep, "in_memory\\PolySplitTEMP", "true")
    PolySplit = arcpy.Sort_management(PolySplitTEMP, "in_memory\\PolySplit", [["Rank_UGO", "ASCENDING"],["Distance","ASCENDING"]])

    ncurrentstep+=1
    arcpy.AddMessage("Converting Split polygon to points - Step " + str(ncurrentstep) + "/" + str(nstep))
    PolySplitToPoint = arcpy.FeatureToPoint_management(PolySplit, "in_memory\\PolySplitToPoint", "INSIDE")

    #/creating the Thiessen polygons and the centerline
    ncurrentstep+=1
    arcpy.AddMessage("Creating Thiessen polygons - Step  " + str(ncurrentstep) + "/" + str(nstep))
    ThiessenPoly = arcpy.CreateThiessenPolygons_analysis(PolySplitToPoint, "in_memory\\ThiessenPoly", "ALL")

    JoinTEMP = arcpy.SpatialJoin_analysis(ThiessenPoly, PolySplitToPoint, "in_memory\\JoinTEMP", "JOIN_ONE_TO_ONE", "KEEP_ALL", "Rank_UGO \"Rank_UGO\" true true false 4 Long 0 0 ,First,#, in_memory\\PolySplitToPoint,Rank_UGO,-1,-1; Distance \"Distance\" true true false 4 Long 0 0 ,First,#,in_memory\\PolySplitToPoint,Distance,-1,-1", "INTERSECT", "", "")
    Join = arcpy.Sort_management(JoinTEMP, "in_memory\\Join", [["Rank_UGO", "ASCENDING"],["Distance","ASCENDING"]])

    ncurrentstep+=1
    arcpy.AddMessage("Merging Thiessen polygons - Step  " + str(ncurrentstep) + "/" + str(nstep))
    Dissolve1 = arcpy.Dissolve_management(Join, "in_memory\\Dissolve1", "Rank_UGO", "", "MULTI_PART", "DISSOLVE_LINES")

    ncurrentstep+=1
    arcpy.AddMessage("Finalizing the centerline - Step  " + str(ncurrentstep) + "/" + str(nstep))
    Dissolve1ToLine = arcpy.Intersect_analysis([Dissolve1,Dissolve1], "in_memory\\Dissolve1ToLine", "", "", "LINE")
    UPD_SL.UpToDateShapeLengthField(Dissolve1ToLine)
    arcpy.DeleteIdentical_management(Dissolve1ToLine, ["Shape_Length"])

    RawCenterline = arcpy.Intersect_analysis([Dissolve1ToLine, Polygon], "in_memory\\RawCenterline", "ALL", "", "INPUT")

    ncurrentstep+=1
    arcpy.AddMessage("Smoothing centerline - Step " + str(ncurrentstep) + "/" + str(nstep))
    Centerline = arcpy.SmoothLine_cartography(RawCenterline, Output, "PAEK", Smoothing, "FIXED_CLOSED_ENDPOINT", "NO_CHECK")

    #/deleting residual fields
    try :
        arcpy.DeleteField_management(Centerline, ["FID_Dissolve1ToLine", "FID_Dissolve1", "FID_Dissolve1_1", "ORIG_FID", "Rank_UGO", "Rank_UGO_1", "FID_"+str(name)])
    except:
        pass
    try : 
        arcpy.DeleteField_management(Centerline, ["FID_Dissol", "FID_Diss_1", "FID_Diss_2", "FID_"+str(name)[0:6], "ORIG_FID", "Rank_UGO", "Rank_UGO_1", "Shape_Leng", "Shape_Le_1"])
    except :
        pass


    #===============================================================================
    # DELETING TEMPORARY FILES
    #===============================================================================
    ncurrentstep+=1
    arcpy.AddMessage("Deleting temporary files - Step " + str(ncurrentstep) + "/" + str(nstep))
    ClearInMemory.main()
    return

# main(Polygon,Polyline,DisaggregationStep,Smoothing,Output)