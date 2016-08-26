# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Confinement Tool                                               #
# Purpose:     Tools for and calculating confinement on a stream              # 
#              network or using a moving window  along the stream network     #  
#                                                                             #
# Authors:     Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Version:     1                                                              #
# Released:                                                                   #
#                                                                             #
# License:     Free to use.                                                   #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import arcpy
from os import path
import ValleyConfinement
import MovingWindow
import Confinement_V2

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Confinement Toolbox"
        self.alias = 'Confinement'
        self.description = "Tools for generating Valley Confinement."

        # List of tool classes associated with this toolbox
        self.tools = [ConfinementTool,
                      #ConfinementTool2,
                      MovingWindowTool]

# Stream Network Management Tools #

# Geomorphic Attributes Tools #
class MovingWindowTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Moving Window Analysis"
        self.description = "Calculate the Valley Confinement using a Moving Window on a Raw Confinement Polyline FC.  Tool Documentation: https://bitbucket.org/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/MovingWindow"
        self.canRunInBackground = True

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

class ConfinementTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Confinement Tool"
        self.description = "Calculate the Confinement for segmented reaches using the Stream Network, Channel Buffer Polygon, and Valley Bottom Polygon."
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        

        paramSwitch = arcpy.Parameter(
            displayName="Results Type",
            name="ResutlsFlag",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        paramSwitch.filter.list = ["Full","Converged Margins Only"]
        
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

        return [param0,param1,param2,param3,param4,param5,param6,paramSwitch]

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

        
        if p[7].valueAsText == "Full":
            ValleyConfinement.main(p[0].valueAsText,
                               p[1].valueAsText,
                               p[2].valueAsText,
                               p[3].valueAsText,
                               p[4].valueAsText,
                               p[5].valueAsText,
                               getTempWorkspace(p[6].valueAsText))
        else:
            reload(Confinement_V2)
            setEnvironmentSettings()

            Confinement_V2.main(p[0].valueAsText,
                               p[1].valueAsText,
                               p[2].valueAsText,
                               p[3].valueAsText,
                               p[4].valueAsText,
                               p[5].valueAsText,
                               getTempWorkspace(p[6].valueAsText))
        
        return

class ConfinementTool2(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Confinement 2"
        self.description = "Calculate the Confinement for segmented reaches using the Stream Network, Channel Buffer Polygon, and Valley Bottom Polygon."
        self.canRunInBackground = True

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
            name="ScratchWorkspace",
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
        reload(Confinement_V2)
        setEnvironmentSettings()

        Confinement_V2.main(p[0].valueAsText,
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