# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Stream Network and Riverstyles Toolbox                         #
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
# Version:     1.3                                                            #
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
#import NetworkSegmentation
#import DynamicSegmentation
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

strCatagoryStreamNetworkManagement = "Stream Network Management Tools"
strCatagoryGeomorphicAnalysis = "Geomorphic Network Analysis Tools"
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
                      CheckNetworkConnectivityTool,
                      FindBraidedNetworkTool,
                      FindCrossingLinesTool,
                      #BuildNetworkTopologyTool,
                      #NetworkSegmentationTool,
                      #DynamicSegmentationTool,
                      #CalculateGeomorphicAttributesTool,
                      ConfinementTool,
                      PlanformTool,
                      SinuosityTool,
                      DividePolygonBySegmentsTool,
                      TransferLineAttributesTool,
                      FluvialCorridorCenterlineTool,
                      CombineAttributesTool,
                      MovingWindowTool,
                      OutsideValleyBottomTool,
                      CopyBranchIDTool,
                      FindDanglesandDuplicatesTool]

# Stream Network Management Tools #

class CheckNetworkConnectivityTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Check Network Connectivity"
        self.description = "Check to make sure all segments in a network are connected."
        self.canRunInBackground = True
        self.category = strCatagoryStreamNetworkManagement

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

class FindBraidedNetworkTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find Braids In Stream Network"
        self.description = "Find braided segments in a stream network."
        self.canRunInBackground = True
        self.category = strCatagoryStreamNetworkManagement

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
        self.category = strCatagoryStreamNetworkManagement

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

        param2 = arcpy.Parameter(
            displayName="Clear Network Table?",
            name="ClearTable",
            datatype="GPBoolean", #Boolean
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
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        reload(BuildNetworkTopology)
        BuildNetworkTopology.main(parameters[0].valueAsText,parameters[1].valueAsText,parameters[2])

        return

class FindCrossingLinesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find Crossing Network Lines"
        self.description = ""
        self.canRunInBackground = True
        self.category = strCatagoryStreamNetworkManagement

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
        self.category = strCatagoryStreamNetworkManagement

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
            direction="Input")

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
        self.category = strCatagoryStreamNetworkManagement

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
        self.category = strCatagoryStreamNetworkManagement

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Stream Network",
            name="InputStreamNetwork",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Downstream Reach ID",
            name="DownstreamReach",
            datatype="GPLong", #Integer
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Output Line Network with Stream Order",
            name="outputStreamOrderFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param2.filter.list = ["Polyline"]

        param3 = arcpy.Parameter(
            displayName="Output Junction Points",
            name="outputJunctionPointsFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param3.filter.list = ["Point"]

        param4 = arcpy.Parameter(
            displayName="Scratch Workspace",
            name="InputTempWorkspace",
            datatype="DEWorkspace", 
            parameterType="Optional",
            direction="Input")
        param4.filter.list = ["Local Database"]
        param4.value = str(arcpy.env.scratchWorkspace)

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
        self.category = strCatagoryStreamNetworkManagement

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
            displayName="Stream (GNIS) Name Field",
            name="fieldStreamName",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Output Line Network with Branch ID",
            name="outputStreamOrderFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param3.filter.list = ["Polyline"]

        param4 = arcpy.Parameter(
            displayName="Scratch Workspace",
            name="InputTempWorkspace",
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

        if parameters[0].value:
            if arcpy.Exists(parameters[0].value):
                # Get Fields
                fields = arcpy.Describe(parameters[0].value).fields
                listFields = []
                for f in fields:
                    listFields.append(f.name)
                parameters[2].filter.list=listFields
                if not parameters[2].altered:
                    if "GNIS_Name" in listFields:
                        parameters[2].value="GNIS_Name"
            else:
                parameters[2].filter.list=[]
                parameters[0].setErrorMessage("Dataset does not exist.")

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        testProjected(parameters[0])
        testProjected(parameters[1])

        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(GenerateStreamBranches)
        GenerateStreamBranches.main(p[0].valueAsText,
                                    p[1].valueAsText,
                                    p[2].valueAsText,
                                    p[3].valueAsText,
                                    getTempWorkspace(p[4].valueAsText))
        return

class CopyBranchIDTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Copy Stream BranchIDs"
        self.description = "Copy the Stream Branch ID from one Network to another."
        self.canRunInBackground = True
        self.category = strCatagoryStreamNetworkManagement

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
            displayName="Output Line Network with Branch ID",
            name="outputStreamOrderFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param3.filter.list = ["Polyline"]

        param4 = arcpy.Parameter(
            displayName="Scratch Workspace",
            name="ScratchWorkspace",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input")

        return [param0,param1,param2,param3,param4]

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
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        reload(CopyBranchID)
        CopyBranchID.main(parameters[0].valueAsText,
                          parameters[1].valueAsText,
                          parameters[2].valueAsText,
                          parameters[3].valueAsText,
                          getTempWorkspace(parameters[4].valueAsText))

        return

# Geomorphic Attributes Tools #
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
            displayName="Input Segmented Stream Network",
            name="InputFCCenterline",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Input Valley Bottom Polygon",
            name="InputConfinementEdges",
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
            displayName="Output Line Network Confinement Feature Class",
            name="outputConCenterlineFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param3.filter.list = ["Polyline"]

        param4 = arcpy.Parameter(
            displayName="Output Confinement by Segments Feature Class",
            name="outputConSegmentsFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param4.filter.list = ["Polyline"]

        param5 = arcpy.Parameter(
            displayName="Calculate Confinement for each Segment?",
            name="boolCalculateConfinement",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        param5.value = True

        param6 = arcpy.Parameter(
            displayName="Channel Polygon Is Already Segmented?",
            name="boolChannelPolygonSegmented",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        #param6.value = False

        param7 = arcpy.Parameter(
            displayName="Scratch Workspace",
            name="InputTempWorkspace",
            datatype="DEWorkspace", 
            parameterType="Optional",
            direction="Input")
        param7.filter.list = ["Local Database"]

        param8 = arcpy.Parameter(
            displayName="Maximum Cross Section Width (Meters)",
            name="CrossSectionLength",
            datatype="GPDouble", 
            parameterType="Optional",
            direction="Input")
        param8.value = "200.00"

        return [param0,param1,param2,param3,param4,param5,param6,param7,param8]

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
                               p[6].valueAsText,
                               getTempWorkspace(p[7].valueAsText),
                               p[8].valueAsText)
        return

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
            displayName="Output Stream Netwokr with Planform Attribute",
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

class CombineAttributesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Combine Attributes"
        self.description = "Combine line attributes from multiple networks into a single feature class."
        self.canRunInBackground = True
        self.category = strCatagoryGeomorphicAnalysis

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Line Networks",
            name="InputFCList",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input",
            multiValue=True)
        param0.filter.list = ["Polyline"]
        
        param1 = arcpy.Parameter(
            displayName="Bounding or Buffer Polygon",
            name="InputFCBounding Polygon",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polygon"] 
        
        param2 = arcpy.Parameter(
            displayName="Is Polygon Segmented?",
            name="InputBoolIsSegmented",
            datatype="GPBoolean", 
            parameterType="Optional",
            direction="Input")
        param2.value = False

        param3 = arcpy.Parameter(
            displayName="Output Line Network",
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

# Utilities #

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

class TransferLineAttributesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Transfer Line Attributes"
        self.description = "Transfer Line Attributes from one network to another."
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
            displayName="Polygon",
            name="InputPolygon",
            datatype="DEFeatureClass", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polygon"]

        param1 = arcpy.Parameter(
            displayName="Polyline",
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
            displayName="Smoothing",
            name="InputSmoothing",
            datatype="GPLong", 
            parameterType="Required",
            direction="Input") 

        param4 = arcpy.Parameter(
            displayName="Output",
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

#### Not Currently Used ###
class NetworkSegmentationTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Stream Network Segmentation"
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
            displayName="Downstream Reach ID",
            name="DownstreamReach",
            datatype="GPLong", #Integer
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Input Vally Bottom Polygon",
            name="InputValleyBottom",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Polygon"]

        param3 = arcpy.Parameter(
            displayName="DEM",
            name="rasterDEM",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Minimum Segment Length",
            name="minSegmentLength",
            datatype="GPDouble", #Boolean
            parameterType="Required",
            direction="Input")

        param5 = arcpy.Parameter(
            displayName="Maximum Number of Segments Per Reach",
            name="maxSegmentsPerReach",
            datatype="GPLong", #Boolean
            parameterType="Required",
            direction="Input")

        param6 = arcpy.Parameter(
            displayName="Slope Threshold",
            name="slopeThreshold",
            datatype="GPDouble", #Boolean
            parameterType="Required",
            direction="Input")

        param7 = arcpy.Parameter(
            displayName="Valley Width Threshold",
            name="valleywidthThreshold",
            datatype="GPDouble", #Boolean
            parameterType="Required",
            direction="Input")

        return [param0,param1,param2,param3,param4,param5,param6,param7]

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
        reload(NetworkSegmentation)
        NetworkSegmentation.main(p[0].valueAsText,
                                 p[1].valueAsText,
                                 p[2].valueAsText,
                                 p[3].valueAsText,
                                 p[4].valueAsText,
                                 p[5].valueAsText,
                                 p[6].valueAsText,
                                 p[7].valueAsText)

        return

class DynamicSegmentationTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Dynamic Segmentation"
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
            displayName="Input Valley Bottom Centerline",
            name="InputValleyCenterline",
            datatype="GPFeatureLayer", #Integer
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polyline"]

        param2 = arcpy.Parameter(
            displayName="Input Vally Bottom Polygon",
            name="InputValleyBottom",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Polygon"]

        param3 = arcpy.Parameter(
            displayName="DEM",
            name="rasterDEM",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Valley Width Bin Type",
            name="ValleyBin",
            datatype="GPString", #Boolean
            parameterType="Required",
            direction="Input")
        param4.filter.list = ["EqualInterval"]
        param4.value = "EqualInterval"

        param5 = arcpy.Parameter(
            displayName="Valley Bin Value",
            name="ValleyBinValue",
            datatype="GPDouble", #Boolean
            parameterType="Required",
            direction="Input")

        param6 = arcpy.Parameter(
            displayName="Slope Threshold",
            name="slopeThreshold",
            datatype="GPDouble", #Boolean
            parameterType="Required",
            direction="Input")
        param6.value = "0.1"

        param7 = arcpy.Parameter(
            displayName="Valley Width Threshold",
            name="valleywidthThreshold",
            datatype="GPDouble", #Boolean
            parameterType="Required",
            direction="Input")
        param7.value = "10"

        return [param0,param1,param2,param3,param4,param5,param6,param7]

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
        reload(DynamicSegmentation)
        DynamicSegmentation.main(p[0].valueAsText,
                                 p[1].valueAsText,
                                 p[2].valueAsText,
                                 p[3].valueAsText,
                                 p[4].valueAsText,
                                 p[5].valueAsText,
                                 p[6].valueAsText,
                                 p[7].valueAsText)

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
            else:
                parameterField.value=""
        else:
            parameterField.filter.list=[]
            parameterSource.setErrorMessage(" Dataset does not exist.")

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
