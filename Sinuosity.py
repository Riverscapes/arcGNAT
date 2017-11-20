# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Channel Sinuosity                                              #
# Purpose:     Calculate channel sinuosity of a stream network feature class. #
#              Please note, this tool can calculate sinuosity for any linear  #
#              feature class, including valley centerlines.                   #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              Jesse Langdon (jesse@southforkresearch.org                     #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Modified:    2017-Nov-17                                                    #
#                                                                             #
# Copyright:   (c) South Fork Research, Inc. 2017                             #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env pythonh

import sys
import arcpy
import gis_tools

arcpy.env.qualifiedFieldNames = False
arcpy.env.overwriteOutput = True

def main(fcInput, fcOutput, fieldName = "C_Sin", workspaceTmp = "in_memory"):

    # Get list of fields from input feature class
    keepFields = [keepField.name for keepField in arcpy.ListFields(fcInput)]
    keepFields.append(fieldName)
    if workspaceTmp != "in_memory":
        keepFields.append("OBJECTID")
        keepFields.append("Shape_Length")

    # Prepare inputs
    fcInputTmp = gis_tools.newGISDataset(workspaceTmp, "fcIn")
    arcpy.CopyFeatures_management(fcInput, fcInputTmp)
    fieldInputID = gis_tools.resetField(fcInputTmp, "InputID", "DOUBLE")
    arcpy.CalculateField_management(fcInputTmp,
                                    fieldInputID,
                                    "!" + arcpy.Describe(fcInputTmp).OIDFieldName + "!",
                                    "PYTHON_9.3")
    fieldSinuosity = gis_tools.resetField(fcInputTmp, fieldName, "DOUBLE")
    fieldSegmentLength = gis_tools.resetField(fcInputTmp, "SgLen", "DOUBLE")

    # Find length of segment
    arcpy.CalculateField_management(fcInputTmp, fieldSegmentLength, "!shape.length!", "PYTHON_9.3")

    # Find straight line distance
    fcSegmentEnds = gis_tools.newGISDataset(workspaceTmp, "SgEnd")
    arcpy.FeatureVerticesToPoints_management(fcInputTmp, fcSegmentEnds, "BOTH_ENDS")

    fcSegmentDistances = gis_tools.newGISDataset(workspaceTmp, "SgDst")
    arcpy.PointsToLine_management(fcSegmentEnds, fcSegmentDistances, fieldInputID)

    fieldDistance = gis_tools.resetField(fcSegmentDistances, "SgDst", "DOUBLE")
    arcpy.CalculateField_management(fcSegmentDistances, fieldDistance, "!shape.length!", "PYTHON_9.3")

    # Join straight line distance feature class
    lyrInputTmp = gis_tools.newGISDataset("Layer","lyrInputTmp")
    arcpy.MakeFeatureLayer_management(fcInputTmp, lyrInputTmp)
    fieldTmpID = gis_tools.resetField(fcSegmentDistances, "TmpID", "DOUBLE")
    arcpy.CalculateField_management(fcSegmentDistances, fieldTmpID, "!InputID!", "PYTHON_9.3")
    arcpy.AddJoin_management(lyrInputTmp,
                             fieldInputID,
                             fcSegmentDistances,
                             fieldTmpID)

    # Calculate sinuosity
    codeblock = """def calculateSinuosity(length,distance):
        if distance == 0:
            return -9999 
        else:
            return length/distance """
    arcpy.CalculateField_management(lyrInputTmp,
                                    fieldSinuosity,
                                    "calculateSinuosity(!" + fieldSegmentLength + "!, !" + fieldDistance + "!)",
                                    "PYTHON_9.3",
                                    codeblock)

    # Write Temporary polyline feature class to disk
    arcpy.CopyFeatures_management(lyrInputTmp, fcOutput)

    dropFields = [dropField.name for dropField in arcpy.ListFields(fcOutput)]
    arcpy.MakeTableView_management(fcOutput, "fcOutputView")
    for dropField in dropFields:
        if dropField not in keepFields:
            arcpy.DeleteField_management("fcOutputView", dropField)

    return


def calculateSinuosity(dblLengthSegment, dblLengthDistance):
    dblSinuosity = dblLengthSegment / dblLengthDistance
    return dblSinuosity


# Run as a script
if __name__ == "__main__":

    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3])