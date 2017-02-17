# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Geomorphic Network and Analysis Toolbox (GNAT)                 #
# Purpose:     Tools for generating a stream network and for calculating      #
#              geomorphic attributes.                                         #
#                                                                             #
# Authors:     Kelly Whitehead (kelly@southforkresearch.org)                  #
#              Jesse Langdon (jesse@southforkresearch.org)                    #
#              Jean Olson (jean@southforkresearch.org                         #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Version:     2.0 Beta                                                       #
# Revised:     2017-Feb-17                                                    #
# Released:                                                                   #
#                                                                             #
# License:     MIT License                                                    #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import arcpy
from os import path
import BuildNetworkTopology
import FindBraidedNetwork
import ValleyPlanform
import Sinuosity
import DividePolygonBySegment
import TransferAttributesToLine
import StreamOrder
import Centerline
import CombineAttributes
import GenerateStreamBranches
import Segmentation
import FindNetworkFeatures

strCatagoryStreamNetworkPreparation = "Main\\Step 1 - Stream Network Preparation"
strCatagoryStreamNetworkSegmentation = "Main\\Step 2 - Stream Network Segmentation"
strCatagoryGeomorphicAnalysis = "Main\\Step 3 - Geomorphic Attributes"
strCatagoryUtilities = "Utilities"


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Geomorphic Network and Analysis Toolbox"
        self.alias = 'GNAT'
        self.description = "Tools for generating a stream network and for generating geomorphic attributes."

        # List of tool classes associated with this toolbox
        self.tools = [StreamOrderTool,
                      StreamBranchesTool,
                      FindBraidedNetworkTool,
                      BuildNetworkTopologyTool,
                      PlanformTool,
                      SinuosityTool,
                      DividePolygonBySegmentsTool,
                      TransferLineAttributesTool,
                      FluvialCorridorCenterlineTool,
                      CombineAttributesTool,
                      SegmentationTool,
                      FindNetworkFeaturesTool]


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
        validation is performed. This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
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
            displayName="Downstream Reach Object ID",
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
        validation is performed. This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        reload(BuildNetworkTopology)
        BuildNetworkTopology.main(parameters[0].valueAsText,parameters[1].valueAsText)
        return


class TransferLineAttributesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Transfer Line Attributes"
        self.description = "Transfer polyline attributes from one network polyine feature class to another with similar geometry."
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="""Input "From" polyline feature class""",
            name="InputFCFromLine",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="""Input "To" polyline feature class""",
            name="InputFCToLine",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polyline"]

        param2 = arcpy.Parameter(
            displayName="Output polyline feature class",
            name="OutputFCLineNetwork",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param2.filter.list = ["Polyline"]

        param3 = arcpy.Parameter(
            displayName="Scratch workspace",
            name="scratchWorkspace",
            datatype="DEWorkspace", 
            parameterType="Optional",
            direction="Input")
        param3.filter.list = ["Local Database"]
        
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
        testProjected(parameters[1])
        testWorkspacePath(parameters[3])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(TransferAttributesToLine)
        setEnvironmentSettings()

        TransferAttributesToLine.main(p[0].valueAsText,
                                      p[1].valueAsText,
                                      p[2].valueAsText,
                                      getTempWorkspace(p[3].valueAsText))

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
            displayName="Merge attributes and geometry from input stream network with output?",
            name="boolMerge",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        param6 = arcpy.Parameter(
            displayName="Output Segmented Line Network",
            name="outputStreamOrderFC",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output")
        param6.filter.list = ["Polyline"]

        return [param0,param1,param2,param3,param4,param5,param6]

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
                          p[5].valueAsText,
                          p[6].valueAsText)
        return


# Geomorphic Attributes Tools
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


# Utilities
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
        self.label = "Sinuosity by Stream Segment"
        self.description = "Calculate Sinuosity in a polyline feature class by segment"
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input stream network or centerline polyline feature class",
            name="InputFCCenterline",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Output polyline feature class with sinousity",
            name="OutputFCCenterline",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param1.filter.list = ["Polyline"]

        param2 = arcpy.Parameter(
            displayName="Sinuosity attribute field name",
            name="InputFieldNameSinuosity",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param2.value = "Sinuosity"

        param3 = arcpy.Parameter(
            displayName="Scratch workspace",
            name="scratchWorkspace",
            datatype="DEWorkspace", 
            parameterType="Optional",
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
        testWorkspacePath(parameters[3])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(Sinuosity)
        setEnvironmentSettings()

        Sinuosity.main(
            p[0].valueAsText,
            p[1].valueAsText,
            p[2].valueAsText,
            getTempWorkspace(p[3].valueAsText))

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
            displayName="Segmented Polyline Feature Class",
            name="InputFCCenterline",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Polygon Feature Class to Segment",
            name="InputFCPolygon",
            datatype="GPFeatureLayer", 
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polygon"]       
        
        param2 = arcpy.Parameter(
            displayName="Output Segmented Polygon Feature Class",
            name="fcSegmentedPolygons",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param2.filter.list = ["Polygon"]

        param3 = arcpy.Parameter(
            displayName="Centerline Point Density (Meters)",
            name="DoublePointDensity",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")
        param3.value = "10.0"

        param4 = arcpy.Parameter(
            displayName="Junction Buffer Distance (Meters)",
            name="dblJunctionBuffer",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")
        param4.value = "120"
        
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
        testWorkspacePath(parameters[3])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(DividePolygonBySegment)
        DividePolygonBySegment.main(p[0].valueAsText,
                                    p[1].valueAsText,
                                    p[2].valueAsText,
                                    p[3].valueAsText,
                                    p[4].valueAsText)

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


class FindNetworkFeaturesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find Network Features"
        self.description = "Find topological features and errors in a stream network feature class."
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
            displayName="Downstream Reach Object ID",
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
        reload(FindNetworkFeatures)
        FindNetworkFeatures.main(p[0].valueAsText,
                        p[1].valueAsText,
                        p[2].valueAsText)

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
                parameter.setWarningMessage("Input " + parameter.name + " should not be M-enabled. Make sure to Disable M-values in the Environment Settings for this tool.")
                return False
            else:
                return True

def populateFields(parameterSource,parameterField,strDefaultFieldName):
    if parameterSource.value:
        if arcpy.Exists(parameterSource.value):
            # Get fields
            fields = arcpy.Describe(parameterSource.value).fields
            listFields = []
            for f in fields:
                listFields.append(f.name)
            parameterField.filter.list=listFields
            if strDefaultFieldName in listFields:
                parameterField.value=strDefaultFieldName
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