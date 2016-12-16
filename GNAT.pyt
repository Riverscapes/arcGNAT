# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Geomorphic Network and Analysis Toolbox (GNAT)                 #
# Purpose:     Tools for generating a Stream Network and for calculating      #  
#              Riverstyles Metrics.                                           #
#                                                                             #
# Authors:     Kelly Whitehead (kelly@southforkresearch.org)                  #
#              Jesse Langdon (jesse@southforkresearch.org)                    #
#              Jean Olson (jean@southforkresearch.org                         #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Version:     2.0 Beta                                                       #
# Released:                                                                   #
#                                                                             #
# License:     Free to use.                                                   #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import arcpy
from os import path
import BuildNetworkTopology
import FindBraidedNetwork
import CheckNetworkConnectivity
import ValleyConfinement
import ValleyPlanform
import Sinuosity
import DividePolygonBySegment
import TransferAttributesToLine
import StreamOrder
import Centerline
import CombineAttributes
import MovingWindow
import FindCrossingLines
import GenerateStreamBranches
import OutsideValleyBottom
import CopyBranchID
import FindDangles
import Segmentation
import FindErrors

strCatagoryStreamNetworkPreparation = "Main\\Step 1 - Stream Network Preparation"
strCatagoryStreamNetworkSegmentation = "Main\\Step 2 - Stream Network Segmentation"
#strCatagoryTransferAttributes = "Main\\3 Attribute Management"
strCatagoryGeomorphicAnalysis = "Main\\Step 3 - Geomorphic Attributes"
strCatagoryUtilities = "Utilities"


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Geomorphic Network and Analysis Toolbox"
        self.alias = 'GNAT'
        self.description = "Tools for generating a Stream Network and for generating Geomorphic Attributes."

        # List of tool classes associated with this toolbox
        self.tools = [StreamOrderTool,
                      StreamBranchesTool,
                      #CheckNetworkConnectivityTool,
                      FindBraidedNetworkTool,
                      #FindCrossingLinesTool,
                      BuildNetworkTopologyTool,
                      #CalculateGeomorphicAttributesTool,
                      #ConfinementTool,
                      PlanformTool,
                      SinuosityTool,
                      DividePolygonBySegmentsTool,
                      TransferLineAttributesTool,
                      FluvialCorridorCenterlineTool,
                      CombineAttributesTool,
                      #MovingWindowTool,
                      OutsideValleyBottomTool,
                      CopyBranchIDTool,
                      #FindDanglesandDuplicatesTool,
                      SegmentationTool,
                      FindErrorsTool]

# Stream Network Prep Tools #
class FindBraidedNetworkTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find Braids In Stream Network"
        self.description = "Find braided segments in a stream network."
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Stream Network",
            name="InputStreamNetwork",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        return [param0]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        
        testProjected(parameters[0])
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        reload(FindBraidedNetwork)
        FindBraidedNetwork.main(parameters[0].valueAsText)

        return

class BuildNetworkTopologyTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Build Network Topology Table"
        self.description = ""
        self.canRunInBackground = True
        self.category = strCatagoryStreamNetworkPreparation

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Stream Network",
            name="InputStreamNetwork",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Downstream Reach",
            name="DownstreamReach",
            datatype="GPLong", #Integer
            parameterType="Required",
            direction="Input")

        return [param0,param1]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        reload(BuildNetworkTopology)
        BuildNetworkTopology.main(parameters[0].valueAsText,parameters[1].valueAsText)
        return

# Transfer Attributes Tools
class CopyBranchIDTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Copy Stream BranchIDs"
        self.description = "Copy the Stream Branch ID from one Network to another."
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            displayName="Input Stream Network with BranchID",
            name="InputStreamNetwork",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Stream Branch ID Field",
            name="fieldBranchID",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        param2 = arcpy.Parameter(
            displayName="Input Target Line Network",
            name="TargetLineNetwork",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Polyline"]
        
        param3 = arcpy.Parameter(
            displayName="Search Radius",
            name="inputSearchRadius",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")
        
        param4 = arcpy.Parameter(
            displayName="Output Line Network with Branch ID",
            name="outputStreamOrderFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param4.filter.list = ["Polyline"]

        param5 = arcpy.Parameter(
            displayName="Scratch Workspace",
            name="ScratchWorkspace",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input")

        return [param0,param1,param2,param3,param4,param5]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        populateFields(parameters[0],parameters[1],"BranchID")
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        
        testProjected(parameters[0])
        testProjected(parameters[2])
        testWorkspacePath(parameters[5])
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        reload(CopyBranchID)
        CopyBranchID.main(parameters[0].valueAsText,
                          parameters[1].valueAsText,
                          parameters[2].valueAsText,
                          parameters[3].valueAsText,
                          parameters[4].valueAsText,
                          getTempWorkspace(parameters[5].valueAsText))

        return

class TransferLineAttributesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Transfer Line Attributes"
        self.description = "Transfer Line Attributes from one network to another of a different geometry."
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="""Input "From" Line Network""",
            name="InputFCFromLine",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="""Input "To" Line Network""",
            name="InputFCToLine",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polyline"]
        
        param2 = arcpy.Parameter(
            displayName="Stream Branch ID Field",
            name="fieldBranchID",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        #param3 = arcpy.Parameter(
        #    displayName="Is Polygon Segmented?",
        #    name="InputBoolIsSegmented",
        #    datatype="GPBoolean", 
        #    parameterType="Optional",
        #    direction="Input")
        #param3.value = False

        param3 = arcpy.Parameter(
            displayName="Output Line Network",
            name="OutputFCLineNetwork",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param3.filter.list = ["Polyline"]

        param4 = arcpy.Parameter(
            displayName="Save Temp Files to Scratch Workspace",
            name="scratchWorkspace",
            datatype="DEWorkspace", 
            parameterType="Optional",
            direction="Input")
        param4.filter.list = ["Local Database"]
        
        return [param0,param1,param2,param3,param4]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        testProjected(parameters[0])
        testProjected(parameters[1])
        if not parameters[2].altered:
            populateFields(parameters[0],parameters[2],"StreamBranchID")
        testWorkspacePath(parameters[4])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(TransferAttributesToLine)
        setEnvironmentSettings()

        TransferAttributesToLine.main(p[0].valueAsText,
                                      p[1].valueAsText,
                                      p[2].valueAsText,
                                      p[3].valueAsText,
                                      getTempWorkspace(p[4].valueAsText))

        return

class CombineAttributesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Combine Attributes"
        self.description = "Merge network attributes in different datasets into a single feature class."
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input polyline feature classes",
            name="InputFCList",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input",
            multiValue=True)
        param0.filter.list = ["Polyline"]
        
        param1 = arcpy.Parameter(
            displayName="Bounding or buffer polygon feature class",
            name="InputFCBounding Polygon",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polygon"] 
        
        param2 = arcpy.Parameter(
            displayName="Is polygon segmented?",
            name="InputBoolIsSegmented",
            datatype="GPBoolean", 
            parameterType="Optional",
            direction="Input")
        param2.value = False

        param3 = arcpy.Parameter(
            displayName="Output polyline feature class",
            name="OutputFCCombinedNetwork",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param3.filter.list = ["Polyline"]
        
        return [param0,param1,param2,param3]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(CombineAttributes)
        setEnvironmentSettings()

        CombineAttributes.main(p[0].values,
                                p[1].valueAsText,
                                p[2].valueAsText,
                                p[3].valueAsText)

        return

# Stream Segmentation
class SegmentationTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Segment Stream Network"
        self.description = "Segment a stream network polyline feature class."
        self.canRunInBackground = True
        self.category = strCatagoryStreamNetworkSegmentation

    def getParameterInfo(self):
        """Define parameter definitions"""
        reload(Segmentation)
        
        param0 = arcpy.Parameter(
            displayName="Stream Network Polyline Feature Class",
            name="InputStreamNetwork",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Segment Length (Meters)",
            name="InputSegmentDistance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param1.value = "200"

        param2 = arcpy.Parameter(
            displayName="Downstream Reach ID",
            name="reachID",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Stream Name Field",
            name="streamIndex",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param3.parameterDependencies = [param0.name]

        param4 = arcpy.Parameter(
            displayName="Segmentation Method",
            name="strSegmentationMethod",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param4.filter.list = Segmentation.listStrSegMethod

        param5 = arcpy.Parameter(
            displayName="Output Segmented Line Network",
            name="outputStreamOrderFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param5.filter.list = ["Polyline"]

        return [param0,param1,param2,param3,param4,param5]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        #populateFields(parameters[0],parameters[3],"BranchID")

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        
        testLayerSelection(parameters[0])
        testProjected(parameters[0])
        testWorkspacePath(parameters[5])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(Segmentation)
        Segmentation.main(p[0].valueAsText,
                          p[1].valueAsText,
                          p[2].valueAsText,
                          p[3].valueAsText,
                          p[4].valueAsText,
                          p[5].valueAsText)
        return

# Geomorphic Attributes Tools #
class PlanformTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Stream Sinuosity and Planform"
        self.description = ""
        self.canRunInBackground = True
        self.category = strCatagoryGeomorphicAnalysis

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Segmented Stream Network",
            name="InputFCStreamNetwork",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Input Segmented Valley Centerline",
            name="InputFCValleyCenterline",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polyline"]

        param2 = arcpy.Parameter(
            displayName="Input Valley Bottom Polygon",
            name="InputFCValleyPolygon",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Polygon"]

        param3 = arcpy.Parameter(
            displayName="Output Stream Network with Sinuosity Attribute",
            name="OutputFCCenterline",
            datatype="DEFeatureClass", 
            parameterType="Required",
            direction="Output")
        param3.filter.list = ["Polyline"]

        param4 = arcpy.Parameter(
            displayName="Output Valley Centerline with Sinuosity Attribute",
            name="OutputFCValleyCenterline",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param4.filter.list = ["Polyline"]

        param5 = arcpy.Parameter(
            displayName="Output Stream Network with Planform Attribute",
            name="OutputFCPlanformCenterline",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param5.filter.list = ["Polyline"]

        param6 = arcpy.Parameter(
            displayName="Scratch Workspace",
            name="scratchWorkspace",
            datatype="DEWorkspace", 
            parameterType="Optional",
            direction="Input")
        param3.filter.list = ["Local Database"]
        
        return [param0,param1,param2,param3,param4,param5,param6]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        testWorkspacePath(parameters[6])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(ValleyPlanform)
        setEnvironmentSettings()

        ValleyPlanform.main(p[0].valueAsText,
                            p[1].valueAsText,
                            p[2].valueAsText,
                            p[3].valueAsText,
                            p[4].valueAsText,
                            p[5].valueAsText,
                            getTempWorkspace(p[6].valueAsText))
        return

# Utilities #
class CheckNetworkConnectivityTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Check Network Connectivity"
        self.description = "Check to make sure all segments in a network are connected."
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Stream Network",
            name="InputStreamNetwork",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="ObjectID or FID field",
            name="DownstreamReachField",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Downstream Reach ID",
            name="DownstreamReachID",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")

        return [param0,param1,param2]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        
        if parameters[0].value:
            if arcpy.Exists(parameters[0].value):
                # Get Fields
                fields = arcpy.Describe(parameters[0].value).fields
                listFields = []
                for f in fields:
                    listFields.append(f.name)
                parameters[1].filter.list=listFields
                if "OBJECTID" in listFields:
                    parameters[1].value="OBJECTID"
                elif "FID" in listFields:
                    parameters[1].value="FID"
            else:
                parameters[1].filter.list=[]
                parameters[0].setErrorMessage(" Dataset does not exist.")
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        
        testProjected(parameters[0])
        
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(CheckNetworkConnectivity)
        CheckNetworkConnectivity.main(p[0].valueAsText,
                                      p[1].valueAsText,
                                      p[2].valueAsText)
        return

class FindCrossingLinesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find Crossing Network Lines"
        self.description = ""
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Stream Network",
            name="InputStreamNetwork",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Output Workspace",
            name="Output Workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Output Polygon Name",
            name="Output Polygon",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Scratch Workspace",
            name="ScratchWorkspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        return [param0,param1,param2,param3]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        
        testProjected(parameters[0])
        testWorkspacePath(parameters[3])
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        reload(FindCrossingLines)
        FindCrossingLines.main(parameters[0].valueAsText,
                               parameters[1].valueAsText,
                               parameters[2].valueAsText,
                               parameters[3].valueAsText)

        return

class OutsideValleyBottomTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find Network Outside Polygon"
        self.description = ""
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            displayName="Input Stream Network",
            name="InputStreamNetwork",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Input Valley Bottom Polygon",
            name="InputVBPolygon",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polygon"]
        
        param2 = arcpy.Parameter(
            displayName="Output Workspace",
            name="Output Workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Scratch Workspace",
            name="ScratchWorkspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        
        param4 = arcpy.Parameter(
            displayName="Output Stream Network",
            name="OutputStreamNetwork",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        param5 = arcpy.Parameter(
            displayName="Output Workspace",
            name="strOutputWorkspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        params = [param0,param1,param2,param3,param5,param4]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        
        testProjected(parameters[0])
        testProjected(parameters[1])
        testWorkspacePath(parameters[3])
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        reload(OutsideValleyBottom)
        OutsideValleyBottom.main(parameters[0].valueAsText,
                                 parameters[1].valueAsText,
                                 parameters[2].valueAsText,
                                 parameters[3].valueAsText,
                                 parameters[4].valueAsText)

        return

class FindDanglesandDuplicatesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find Dangles and Remove Duplicates Tool"
        self.description = "Find Sort Line Dangles and Remove Duplicate/Identical Line Segments in the Stream Network"
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            displayName="Input Stream Network",
            name="InputStreamNetwork",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Maximum Dangle Length",
            name="InputMaxDangleLength",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        
        param2 = arcpy.Parameter(
            displayName="Output Workspace",
            name="Output Workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Scratch Workspace",
            name="ScratchWorkspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        return [param0,param1,param2,param3]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        
        testProjected(parameters[0])
        testWorkspacePath(parameters[3])

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        reload(FindDangles)
        FindDangles.main(parameters[0].valueAsText,
                                 parameters[1].valueAsText,
                                 parameters[2].valueAsText,
                                 parameters[3].valueAsText,)

        return

class StreamOrderTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate Stream Order"
        self.description = "Generate Stream Order for the Stream Network."
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input stream network",
            name="InputStreamNetwork",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Downstream reach ID",
            name="DownstreamReach",
            datatype="GPLong", #Integer
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Output network with stream order",
            name="outputStreamOrderFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param2.filter.list = ["Polyline"]

        param3 = arcpy.Parameter(
            displayName="Output junction points",
            name="outputJunctionPointsFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param3.filter.list = ["Point"]

        param4 = arcpy.Parameter(
            displayName="Scratch workspace",
            name="InputTempWorkspace",
            datatype="DEWorkspace", 
            parameterType="Optional",
            direction="Input")
        #param4.filter.list = ["Local Database"]
        #param4.value = str(arcpy.env.scratchWorkspace)

        #listControlParams = GNAT_Control_Parameters()

        return [param0,param1,param2,param3,param4]# + listControlParams

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        testProjected(parameters[0])
        testWorkspacePath(parameters[4])
        return

    def execute(self, p, messages):
        """The source code of the tool."""

        reload(StreamOrder)
        StreamOrder.main(p[0].valueAsText,
                         p[1].valueAsText,
                         p[2].valueAsText,
                         p[3].valueAsText,
                         p[4].valueAsText)
        return

class StreamBranchesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Generate Stream Branches"
        self.description = "Generate Stream Branches for the Stream Network."
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Stream Network (with Stream Order)",
            name="InputStreamNetwork",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Input Junction Points",
            name="InputJunctionPoints",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param1.filter.list = ["Point","Multipoint"]

        param2 = arcpy.Parameter(
            displayName="Primary Stream Name Field (i.e. GNIS Name)",
            name="fieldStreamName",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Stream Order Field",
            name="fieldStreamOrder",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Output Line Network with Branch ID",
            name="outputStreamOrderFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param4.filter.list = ["Polyline"]

        param5 = arcpy.Parameter(
            displayName="Dissolve Output Network by BranchID?",
            name="boolDissolve",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        param6 = arcpy.Parameter(
            displayName="Scratch Workspace",
            name="InputTempWorkspace",
            datatype="DEWorkspace", 
            parameterType="Optional",
            direction="Input")
        param6.filter.list = ["Local Database"]

        return [param0,param1,param2,param3,param4,param5,param6]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        populateFields(parameters[0],parameters[2],"GNIS_Name")
        populateFields(parameters[0],parameters[3],"StreamOrder")

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        testProjected(parameters[0])
        testProjected(parameters[1])
        testLayerSelection(parameters[0])
        testLayerSelection(parameters[1])
        testWorkspacePath(parameters[6])

        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(GenerateStreamBranches)
        GenerateStreamBranches.main(p[0].valueAsText,
                                    p[1].valueAsText,
                                    p[2].valueAsText,
                                    p[3].valueAsText,
                                    p[4].valueAsText,
                                    p[5].valueAsText,
                                    getTempWorkspace(p[6].valueAsText))
        return

class SinuosityTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Sinuosity by Segment"
        self.description = "Calculate Sinuosity in linework by Segment"
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Stream Network or Centerline",
            name="InputFCCenterline",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Sinuosity Field Name",
            name="InputFieldNameSinuosity",
            datatype="GPString", 
            parameterType="Required",
            direction="Input")
        param1.value = "Sinuosity"

        param3 = arcpy.Parameter(
            displayName="Save Temp Files to Scratch Workspace",
            name="scratchWorkspace",
            datatype="DEWorkspace", 
            parameterType="Optional",
            direction="Input")
        param3.filter.list = ["Local Database"]
        
        return [param0,param1,param3]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        testWorkspacePath(parameters[2])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(Sinuosity)
        setEnvironmentSettings()

        Sinuosity.main(
            p[0].valueAsText,
            p[1].valueAsText,
            getTempWorkspace(p[2].valueAsText))

        return

class DividePolygonBySegmentsTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Divide Polygon by Segments"
        self.description = "Divides a channel or valley polygon by centerline segments using Thiessan Polygons."
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Segmented Centerline of Polygon",
            name="InputFCCenterline",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Polygon to Segment",
            name="InputFCPolygon",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polygon"]       
        
        param2 = arcpy.Parameter(
            displayName="Output Segmented Polygon",
            name="fcSegmentedPolygons",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param2.filter.list = ["Polygon"]

        param3 = arcpy.Parameter(
            displayName="Scratch Workspace",
            name="scratchWorkspace",
            datatype="DEWorkspace", 
            parameterType="Optional",
            direction="Input")
        param3.filter.list = ["Local Database"]

        param4 = arcpy.Parameter(
            displayName="Centerline Point Density (Meters)",
            name="DoublePointDensity",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")
        param4.value = "10.0"

        param5 = arcpy.Parameter(
            displayName="Junction Buffer (Meters)",
            name="dblJunctionBuffer",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")
        param5.value = "120"
        
        return [param0,param1,param2,param3,param4,param5]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        testWorkspacePath(parameters[3])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(DividePolygonBySegment)

        DividePolygonBySegment.main(p[0].valueAsText,
                                    p[1].valueAsText,
                                    p[2].valueAsText,
                                    p[3].valueAsText,
                                    p[4].valueAsText,
                                    p[5].valueAsText)

        return

class FluvialCorridorCenterlineTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Centerline Tool (from Fluvial Corridor Tools)"
        self.description = "Generate a centerline of a polygon using Fluvial Cooridor Centerline Tool"
        self.canRunInBackground = False
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Valley bottom polygon feature class",
            name="InputPolygon",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polygon"]

        param1 = arcpy.Parameter(
            displayName="Stream network polyline feature class",
            name="InputFCPolyline",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polyline"]

        param2 = arcpy.Parameter(
            displayName="Disaggregation step",
            name="InputDisaggregationStep",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Smoothing tolerance",
            name="InputSmoothing",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Output centerline",
            name="OutputFCPolyline",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        #param4.filter.list = ["Polyline"]

        param5 = arcpy.Parameter(
            displayName="Delete temporary files",
            name="InputDeleteTempFiles",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        return [param0,param1,param2,param3,param4,param5]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(Centerline)
        Centerline.main(p[0].valueAsText,
                                  p[1].valueAsText,
                                  p[2].valueAsText,
                                  p[3].valueAsText,
                                  p[4].valueAsText,
                                  p[5].valueAsText)

        return

class FindErrorsTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find Network Errors Tool"
        self.description = "Find topological errors in a stream network feature class."
        self.canRunInBackground = False
        self.category = strCatagoryStreamNetworkPreparation

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Processed Input Stream Network",
            name="InputStreamNetwork",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Stream Network Table",
            name="StreamNetworkTable",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Downstream Reach ID",
            name="DownstreamReach",
            datatype="GPLong",  # Integer
            parameterType="Required",
            direction="Input")

        return [param0, param1, param2]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(FindErrors)
        FindErrors.main(p[0].valueAsText,
                        p[1].valueAsText,
                        p[2].valueAsText)

        return

#### Not Currently Used ###
class MovingWindowTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Moving Window Analysis"
        self.description = "Calculate the Valley Confinement using a Moving Window on a Raw Confinement Polyline FC.  Tool Documentation: https://bitbucket.org/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/MovingWindow"
        self.canRunInBackground = True
        self.category = strCatagoryGeomorphicAnalysis

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Stream Network with Confinement",
            name="lineNetwork",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Stream Branch ID Field",
            name="fieldStreamID",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Attribute Field (Confinement)",
            name="fieldAttribute",
            datatype="GPString", 
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Seed Point Distance",
            name="dblSeedPointDistance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        #param3.value = 50

        param4 = arcpy.Parameter(
            displayName="Window Sizes",
            name="inputWindowSizes",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        #param4.value = [50,100]

        param5 = arcpy.Parameter(
            displayName="Output Workspace",
            name="strOutputWorkspace",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input",
            category="Outputs")

        param5.value = str(arcpy.env.scratchWorkspace)
        params = [param0,param1,param2,param3,param4,param5]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].value:
            if arcpy.Exists(parameters[0].value):
                # Get Fields
                fields = arcpy.Describe(parameters[0].value).fields
                listFields = []
                for f in fields:
                    listFields.append(f.name)
                parameters[1].filter.list=listFields
                if "BranchID" in listFields:
                    parameters[1].value="BranchID"
                parameters[2].filter.list=listFields
            else:
                parameters[1].filter.list=[]
                parameters[2].filter.list=[]
                parameters[0].setErrorMessage(" Dataset does not exist.")
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        testProjected(parameters[0])
        testWorkspacePath(parameters[5])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(MovingWindow)
        setEnvironmentSettings()

        MovingWindow.main(p[0].valueAsText,
                          p[1].valueAsText,
                          p[2].valueAsText,
                          p[3].valueAsText,
                          p[4].valueAsText,
                          p[5].valueAsText)
        return

class CalculateGeomorphicAttributesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate Geomorphic Attributes"
        self.description = "Calculate Selected Geomorphic for segmented reaches."
        self.canRunInBackground = True
        self.category = strCatagoryGeomorphicAnalysis

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Stream Network (Segmented for Sinuosity/Planform)",
            name="InputFCStreamNetworkSegSin",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Input Stream Network (Segmented for Confinement)",
            name="InputFCStreamNetworkSegCon",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polyline"]

        param2 = arcpy.Parameter(
            displayName="Input Valley Centerline (Segmented for Sinuosity/Planform)",
            name="InputFCValleyCenterline",
            datatype="GPFeatureLayer", 
            parameterType="Optional",
            enabled="True",
            direction="Input")
        param2.filter.list = ["Polyline"]

        param3 = arcpy.Parameter(
            displayName="Input Valley Bottom Polygon",
            name="InputConfinementEdges",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param3.filter.list = ["Polygon"]

        param4 = arcpy.Parameter(
            displayName="Input Channel Polygon",
            name="InputChannelBottom",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param4.filter.list = ["Polygon"]

        param5 = arcpy.Parameter(
            displayName="Output Workspace (RiverStyles GDB)",
            name="InputWorkspace",
            datatype="DEWorkspace", 
            parameterType="Required",
            direction="Input")
        param5.filter.list = ["Local Database"]

        param6 = arcpy.Parameter(
            displayName="RiverStyles Attributes to Calculate",
            name="CalculateRiverstyles",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue="True",
            )
        param6.filter.list = ["Segment Channel Polygon",
                              "Confinement",
                              "Sinuosity",
                              "Planform",
                              "Generate Final Output"]

        return [param0,param1,param2,param3,param4,param5,param6]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        ## Set Parameter Names ##

        setEnvironmentSettings()
        descOutputGDB = arcpy.Describe(p[5].valueAsText)
        outputFolder = descOutputGDB.path

        fcChannelCenterlineSmall = p[1].valueAsText
        fcChannelCenterlineLarge = p[0].valueAsText
        fcValleyCenterline = p[2].valueAsText
        fcChannelPolygonInput = p[4].valueAsText
        fcOutputChannelPolygonSegmented = p[5].valueAsText + "\\SegmentedChannelPolygons"
        fcValleyBottomPolygon = p[3].valueAsText
        fcOutputConfinementLineNetwork = p[5].valueAsText + "\\ConfinementByLineNetwork"
        fcOutputConfinementSegments = p[5].valueAsText + "\\ConfinementBySegments"
        fcOutputChannelSinuosity = p[5].valueAsText + "\\ChannelSinuosity"
        fcOutputValleySinuosity = p[5].valueAsText + "\\ValleySinuosity"
        fcOutputValleyPlanform = p[5].valueAsText + "\\ValleyPlanform"
        fcOutputFinalRiverStyles = p[5].valueAsText + "\\RiverStylesOutput"

        listCombineLineFCs = []

        #SegPolygons tool
        if "Segment Channel Polygon" in p[6].valueAsText:
            arcpy.AddMessage("RiverStyles Attributes: Starting Polygon Segmentation...")
            workspaceSegmentPolygons = arcpy.CreateUniqueName("ScratchPolygonSegments.gdb",descOutputGDB.path)
            arcpy.CreateFileGDB_management(descOutputGDB.path,path.basename(path.splitext(workspaceSegmentPolygons)[0]))

            DividePolygonBySegment.main(fcChannelCenterlineSmall,
                                        fcChannelPolygonInput,
                                        fcOutputChannelPolygonSegmented,
                                        workspaceSegmentPolygons,
                                        "10.0",
                                        "120.0")
        else:
            fcOutputChannelPolygonSegmented = fcChannelPolygonInput

        # Confinement Tool
        if "Confinement" in p[6].valueAsText:
            arcpy.AddMessage("RiverStyles Attributes: Starting Confinement...")
            workspaceConfinement = arcpy.CreateUniqueName("ScratchConfinement.gdb",descOutputGDB.path)
            arcpy.CreateFileGDB_management(descOutputGDB.path,path.basename(path.splitext(workspaceConfinement)[0]))

            ValleyConfinement.main(fcChannelCenterlineSmall,
                                   fcValleyBottomPolygon,
                                   fcOutputChannelPolygonSegmented,
                                   fcOutputConfinementLineNetwork,
                                   fcOutputConfinementSegments,
                                   True,
                                   False,
                                   workspaceConfinement,
                                   "300.00")

        listCombineLineFCs.append(fcOutputConfinementSegments)

        # Planform (Sinuosity Tool)
        if "Planform" in p[6].valueAsText:
            arcpy.AddMessage("RiverStyles Attributes: Starting Planform Calcluation...")
            workspacePlanform = arcpy.CreateUniqueName("ScratchPlanform.gdb",descOutputGDB.path)
            arcpy.CreateFileGDB_management(descOutputGDB.path,path.basename(path.splitext(workspacePlanform)[0]))
            arcpy.env.scratchWorkspace = workspacePlanform

            ValleyPlanform.main(fcChannelCenterlineLarge,
                                fcValleyCenterline,
                                fcfcValleyBottomPolygon,
                                fcOutputChannelSinuosity,
                                fcOutputValleySinuosity,
                                fcOutputValleyPlanform
                                )

            listCombineLineFCs.append(fcOutputValleyPlanform)

        if "Sinuosity" in p[6].valueAsText and "Planform" not in p[6].valueAsText: # do not calculate sinuosity if calculating planform
            arcpy.AddMessage("RiverStyles Attributes: Starting Sinuosity Calcluation...")
            workspaceSinuosity = arcpy.CreateUniqueName("ScratchSinuosity.gdb",descOutputGDB.path)
            arcpy.CreateFileGDB_management(descOutputGDB.path,path.basename(path.splitext(workspaceSinuosity)[0]))
            arcpy.env.scratchWorkspace = workspaceSinuosity

            arcpy.CopyFeatures_management(fcChannelCenterlineLarge,fcOutputChannelSinuosity)
            arcpy.Exists(fcOutputChannelSinuosity)
            Sinuosity.main(fcOutputChannelSinuosity,
                           "Sinuosity")

            listCombineLineFCs.append(fcOutputChannelSinuosity)
        
        if "Generate Final Output" in p[6].valueAsText:
            arcpy.AddMessage("RiverStyles Attributes: Combining Final Attributes...")
            workspaceCombine = arcpy.CreateUniqueName("ScratchCombineAttributes.gdb",descOutputGDB.path)
            arcpy.CreateFileGDB_management(descOutputGDB.path,path.basename(path.splitext(workspaceCombine)[0]))
            arcpy.env.scratchWorkspace = workspaceCombine

            CombineAttributes.main(listCombineLineFCs,fcValleyBottomPolygon,"False",fcOutputFinalRiverStyles)

        return

class ConfinementTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Confinement"
        self.description = "Calculate the Confinement for segmented reaches using the Stream Network, Channel Buffer Polygon, and Valley Bottom Polygon."
        self.canRunInBackground = True
        self.category = strCatagoryGeomorphicAnalysis

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Stream Network (Segmentation Optional)",
            name="InputFCStreamNetwork",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Input Valley Bottom Polygon",
            name="InputValleyBottomPolygon",
            datatype="GPFeatureLayer", #Integer
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polygon"]

        param2 = arcpy.Parameter(
            displayName="Input Channel Polygon",
            name="InputChannelBottom",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Polygon"]

        param3 = arcpy.Parameter(
            displayName="Output Raw Confining State Along Stream Network",
            name="outputConCenterlineFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param3.filter.list = ["Polyline"]

        param4 = arcpy.Parameter(
            displayName="Output Confinement Calculated by Segments",
            name="outputConSegmentsFC",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Output")
        #param4.filter.list = ["Polyline"]

        param5 = arcpy.Parameter(
            displayName="Output Confining Margins",
            name="fcOutputConfiningMargins",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Output")
        #param5.filter.FeatureClass = ["Polyline"]

        param6 = arcpy.Parameter(
            displayName="Scratch Workspace",
            name="InputTempWorkspace",
            datatype="DEWorkspace", 
            parameterType="Optional",
            direction="Input")
        param6.filter.list = ["Local Database"]

        return [param0,param1,param2,param3,param4,param5,param6]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        
        testProjected(parameters[0])
        testProjected(parameters[1])
        testProjected(parameters[2])
        testMValues(parameters[0])
        testMValues(parameters[1])
        testMValues(parameters[2])
        testLayerSelection(parameters[0])
        testLayerSelection(parameters[1])
        testLayerSelection(parameters[2])
        testWorkspacePath(parameters[6])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(ValleyConfinement)
        setEnvironmentSettings()

        ValleyConfinement.main(p[0].valueAsText,
                               p[1].valueAsText,
                               p[2].valueAsText,
                               p[3].valueAsText,
                               p[4].valueAsText,
                               p[5].valueAsText,
                               getTempWorkspace(p[6].valueAsText))
        return

# Other Functions # 
def setEnvironmentSettings():
    arcpy.env.OutputMFlag = "Disabled"
    arcpy.env.OutputZFlag = "Disabled"
     
    return

def getTempWorkspace(strWorkspaceParameter):

    if strWorkspaceParameter == None or strWorkspaceParameter == "":
        return "in_memory"
    else:
       return strWorkspaceParameter

def testProjected(parameter):
    
    # Test Projection
    if parameter.value:
        if arcpy.Exists(parameter.value):
            if arcpy.Describe(parameter.value).spatialReference.type <> u"Projected":
                parameter.setErrorMessage("Input " + parameter.name + " must be in a Projected Coordinate System.")
                return False
            else:
                return True

def testMValues(parameter):
    if parameter.value:
        if arcpy.Exists(parameter.value):
            if arcpy.Describe(parameter.value).hasM is True:
                parameter.setWarningMessage("Input " + parameter.name + " shoud not be M-enabled. Make sure to Disable M-values in the Environment Settings for this tool.")
                return False
            else:
                return True

def populateFields(parameterSource,parameterField,strDefaultFieldName):
    if parameterSource.value:
        if arcpy.Exists(parameterSource.value):
            # Get Fields
            fields = arcpy.Describe(parameterSource.value).fields
            listFields = []
            for f in fields:
                listFields.append(f.name)
            parameterField.filter.list=listFields
            if strDefaultFieldName in listFields:
                parameterField.value=strDefaultFieldName
            #else:
            #    parameterField.value=""
        else:
            parameterField.value=""
            parameterField.filter.list=[]
            parameterSource.setErrorMessage(" Dataset does not exist.")

    return

def testLayerSelection(parameter):
    if parameter.value:
        if arcpy.Exists(parameter.value):
            desc=arcpy.Describe(parameter.value)
            if desc.dataType == "FeatureLayer":
                if desc.FIDSet:
                    parameter.setWarningMessage("Input layer " + parameter.name + " contains a selection. Clear the selection in order to run this tool on all features in the layer.")
    
    return 

def testWorkspacePath(parameterWorkspace):

    if parameterWorkspace.value:
        if arcpy.Exists(parameterWorkspace.value):
            desc = arcpy.Describe(parameterWorkspace.value)
            if desc.dataType == "Workspace" or desc.dataType == "Folder":
                if desc.workspaceType == "LocalDatabase":
                    strPath = desc.path
                elif desc.workspaceType == "FileSystem":
                    strPath = str(parameterWorkspace.value)
                else:
                    parameterWorkspace.setWarningMessage("Cannot identify workspace type for " + parameterWorkspace.name + ".")
                    return
                if " " in strPath:
                    parameterWorkspace.setWarningMessage(parameterWorkspace.name + " contains a space in the file path name and could cause Geoprocessing issues. Please use a different workspace that does not contain a space in the path name.")
    return

#def GNAT_Control_Parameters():

#    param4 = arcpy.Parameter(
#        displayName="Input Channel Polygon",
#        name="InputChannelBottom",
#        datatype="GPFeatureLayer", 
#        parameterType="Required",
#        direction="Input",
#        category="GNAT Options")
#    param4.filter.list = ["Polygon"]

#    param5 = arcpy.Parameter(
#        displayName="Output Workspace (RiverStyles GDB)",
#        name="InputWorkspace",
#        datatype="DEWorkspace", 
#        parameterType="Required",
#        direction="Input",
#        category="GNAT Options")
#    param5.filter.list = ["Local Database"]

#    param6 = arcpy.Parameter(
#        displayName="RiverStyles Attributes to Calculate",
#        name="CalculateRiverstyles",
#        datatype="GPString",
#        parameterType="Required",
#        direction="Input",
#        multiValue="True",
#        category="GNAT Options")

#    return [param4,param5,param6]