# -*- coding: utf-8 -*-

'''
Created on 21 fev. 2013
Last update on 07 fev. 2014

@author: Clement Roux

@contact: clement.roux@ens-lyon.fr
          CNRS - UMR5600 Environnement Ville Societe
          15 Parvis Ren� Descartes, BP 7000, 69342 Lyon Cedex 07, France
         
@note: For each use of the FluvialCorridor toolbox leading to a publication, report, presentation or any other
       document, please refer the following article :
       Roux, C., Alber, A., Bertrand, M., Vaudor, L., Piegay, H., submitted. "FluvialCorridor": A new ArcGIS 
       package for multiscale riverscape exploration. Geomorphology
       
@summary: def__SLEM is an open-source python and arcPy code.
          SLEM (for Split Line Each Meters) is used in several modules of the FluvialCorridor package.
          According a user-defined length (m), named "Distance" in the code, it enables to segment a 
          polyline from upstream to downstream.

          This code has been significantly modified by Jesse Langdon, South Fork Research, Inc. (SFR).
'''


# Import of required librairies
import arcpy
import def__UpToDateShapeLengthField as UPD_SL
import def__Export as Ext

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

#===============================================================================
# CODING
#===============================================================================
#def SLEM(Line, Distance, Output, TempFolder, TF):
def SLEM(Line, Distance, Output, TF):
    
    CopyLine = arcpy.CopyFeatures_management(Line, r"in_memory\CopyLine")
    
    fieldnames = [f.name for f in arcpy.ListFields(CopyLine)]

    #/identification of the polyline type : raw, UGOs, sequenced UGOs, or AGOs
    k = 0
    if "Rank_AGO" in fieldnames :
        k = 3
    elif "Order_ID" in fieldnames :
        k = 2
    elif "Rank_UGO" in fieldnames :
        k = 1
            

    ################################
    ########## Raw polyline ########
    ################################
    if k == 0 :
        
        #/shaping of the segmented result
        arcpy.AddField_management(CopyLine, "Rank_UGO", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(CopyLine, "Rank_UGO", "["+fieldnames[0]+"]", "VB", "")
        arcpy.AddField_management(CopyLine, "From_Measure", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(CopyLine, "From_Measure", "0", "VB", "")
        arcpy.AddField_management(CopyLine, "To_Measure", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(CopyLine, "To_Measure", "!shape.length!", "PYTHON_9.3", "")
        
        #/conversion in routes
        LineRoutes = arcpy.CreateRoutes_lr(CopyLine, "Rank_UGO", r"in_memory\LineRoutes", "TWO_FIELDS", "From_Measure", "To_Measure")

        #/creation of the event table
        PointEventTEMP = arcpy.CreateTable_management("in_memory", "PointEventTEMP", "", "")
        arcpy.AddField_management(PointEventTEMP, "Rank_UGO", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "Distance", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(PointEventTEMP, "To_M", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        
        UPD_SL.UpToDateShapeLengthField(LineRoutes)

        rowslines = arcpy.SearchCursor(LineRoutes)
        rowsevents = arcpy.InsertCursor(PointEventTEMP)
        for line in rowslines:
            tempdistance = float(line.Shape_Length)
            while (tempdistance > float(0)):
                row = rowsevents.newRow()
                row.Rank_UGO = line.Rank_UGO
                row.To_M = max(0, tempdistance - float(Distance))
                row.Distance = tempdistance
                rowsevents.insertRow(row)
                tempdistance = tempdistance - float(Distance)
        del rowslines
        del rowsevents

        #/creation of the route event layer
        MakeRouteEventTEMP = arcpy.MakeRouteEventLayer_lr(LineRoutes, "Rank_UGO", PointEventTEMP,
                                                         "Rank_UGO LINE Distance To_M",
                                                         r"in_memory\MakeRouteEventTEMP")
        Split = arcpy.CopyFeatures_management(MakeRouteEventTEMP, r"in_memory\Split", "", "0", "0", "0")
        Sort = arcpy.Sort_management(Split, Output, [["Rank_UGO", "ASCENDING"], ["Distance", "ASCENDING"]])

        arcpy.DeleteField_management(Sort, "To_M")
        
        #/calculation of the "Distance" field
        UPD_SL.UpToDateShapeLengthField(Sort)
        
        rows1 = arcpy.UpdateCursor(Sort)
        rows2 = arcpy.UpdateCursor(Sort)
        line2 = rows2.next()
        line2.Distance = 0
        rows2.updateRow(line2)
        nrows = int(str(arcpy.GetCount_management(Sort)))
        n = 0
        for line1 in rows1 :
            line2 = rows2.next()          
            if n == nrows-1 :
                break
            if n == 0 :
                line1.Distance = 0
            if line2.Rank_UGO == line1.Rank_UGO :
                line2.Distance = line1.Distance + line1.Shape_Length
                rows2.updateRow(line2)
            if line2.Rank_UGO != line1.Rank_UGO :
                line2.Distance = 0
                rows2.updateRow(line2)
            
            n+=1
        
        #/deleting of the temporary files
        if str(TF) == "true" :
            arcpy.Delete_management(Split)
            arcpy.Delete_management(CopyLine)
            arcpy.Delete_management(LineRoutes)
            arcpy.Delete_management(PointEventTEMP)
    
    return Sort