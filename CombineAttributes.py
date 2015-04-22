# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Combine Attributes Tool                                        #
# Purpose:     Combines attributes from multiple line layers into one layer   #
#                                                                             #
# Author:      Jesse Langdon                                                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Apr-15                                                    #
# Version:     0.1          Modified: 2015-Apr-15                             #
# Copyright:   (c) Jesse Langdon   2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import sys
import arcpy
import gis_tools
import TransferAttributesToLine

# temporary input variables for testing
# fcList = ["C:\\JL\\RiverStyles\\Tools\\NetworkToolbox\\CombineAttributes\\data\\Input.gdb\\strm_1000m_seg_testareas",
# 			"C:\\JL\\RiverStyles\\Tools\\NetworkToolbox\\CombineAttributes\\data\\Input.gdb\\strm_300m_seg_testareas",
# 			"C:\\JL\\RiverStyles\\Tools\\NetworkToolbox\\CombineAttributes\\data\\Input.gdb\\strm_600m_seg_testareas",
# 			"C:\\JL\\RiverStyles\\Tools\\NetworkToolbox\\CombineAttributes\\data\\Input.gdb\\strm_800m_seg_testareas"
# 			]
# fcBndPoly = "C:\\JL\RiverStyles\\Tools\\NetworkToolbox\\CombineAttributes\\data\\Input.gdb\\MF_JD_valley_bottom"
# boolSeg = False
# fcOutCombine = "C:\\JL\\RiverStyles\\Tools\\NetworkToolbox\\CombineAttributes\\data\\Output.gdb\\test_output"

def main(fcList, fcBndPoly, boolSeg, fcOutCombine):
	# removes first item from list of feature classes
	# creates temporary "fcToLine" feature class to serve as input to TransferAttributesToLine function
    fcToLine = fcList.pop(0)

	# iterate though list of remaining feature classes to perform attribute TransferAttributesToLine
    for i in fcList:
        fcToolOutput = TransferAttributesToLine.main(i, fcToLine, fcBndPoly, boolSeg, fcOutCombine)
        fcToLine = fcToolOutput
    return fcToLine

#main(fcList, fcBndPoly, boolSeg, fcOutCombine)