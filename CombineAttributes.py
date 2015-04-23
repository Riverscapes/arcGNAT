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
import TransferAttributesToLine

def main(fcList, fcBndPoly, boolSeg, fcOutCombine):
	# removes first item from list of feature classes
	# creates temporary "fcToLine" feature class to serve as input to TransferAttributesToLine function
    fcToLine = fcList.pop(0)

	# iterate though list of remaining feature classes to perform attribute TransferAttributesToLine
    for i in fcList:
        fcToolOutput = TransferAttributesToLine.main(i, fcToLine, fcBndPoly, boolSeg, fcOutCombine)
        fcToLine = fcToolOutput
    return fcToLine