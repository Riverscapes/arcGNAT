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
# Modified:    2017-Sep-28                                                    #
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

def main(fcStreamNetwork,
         fcValleyCenterline,
         fcValleyBottomPolygon,
         outputFCSinuosityValley,
         workspaceTemp="in_memory"):
    
    # Set workspace and reset modules
    reload(TransferAttributesToLine)
    reload(Sinuosity)

    lyrInputStreamNetwork = "lyrInputStreamNetwork"
    arcpy.MakeFeatureLayer_management(fcStreamNetwork, lyrInputStreamNetwork)

    fieldInputID = gis_tools.resetField(lyrInputStreamNetwork, "InputID", "DOUBLE")
    arcpy.CalculateField_management(lyrInputStreamNetwork,
                                    fieldInputID,
                                    "!" + arcpy.Describe(lyrInputStreamNetwork).OIDFieldName + "!",
                                    "PYTHON_9.3")

    # outputs are stored in the temporary workspace
    outputFCSinuosityChannel = gis_tools.newGISDataset(workspaceTemp, "outputFCSinuosityChannel")
    outputFCPlanform = gis_tools.newGISDataset(workspaceTemp, "outputFCPlanform")

    # Calculate valley sinuosity for each channel network segment
    if arcpy.Exists(outputFCSinuosityChannel):
        arcpy.Delete_management(outputFCSinuosityChannel)
    Sinuosity.main(fcStreamNetwork, outputFCSinuosityChannel, "C_Sin", workspaceTemp)
    
    # Calculate centerline sinuosity for each valley centerline segment
    if arcpy.Exists(outputFCSinuosityValley):
        arcpy.Delete_management(outputFCSinuosityValley)
    Sinuosity.main(fcValleyCenterline, outputFCSinuosityValley, "V_Sin", workspaceTemp)

    # Transfer attributes to stream network polyline feature class
    if arcpy.Exists(outputFCPlanform):
        arcpy.Delete_management(outputFCPlanform)
    TransferAttributesToLine.main(outputFCSinuosityValley,
                                  outputFCSinuosityChannel,
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
                  "InputID",
                  "Planform",
                  "C_Sin",
                  "V_Sin"]
    dropFields = [dropField.name for dropField in arcpy.ListFields(outputFCPlanform)]
    arcpy.MakeTableView_management(outputFCPlanform, "fcOutputView")
    for dropField in dropFields:
        if dropField not in keepFields:
            arcpy.DeleteField_management("fcOutputView", dropField)

    # remove attribute fields if they are found in the input stream network
    attrbFields = ["Planform", "C_Sin", "V_Sin"]
    checkFields = [f.name for f in arcpy.ListFields(lyrInputStreamNetwork)]
    for attrbField in attrbFields:
        if attrbField in checkFields:
            arcpy.DeleteField_management(lyrInputStreamNetwork, attrbField)

    # join final sinuosity/planform output back to input stream network
    arcpy.JoinField_management(lyrInputStreamNetwork,
                               "InputID",
                               "fcOutputView",
                               "InputID",
                               ["C_Sin", "Planform", "V_Sin"])

    return