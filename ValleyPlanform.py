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

import sys
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