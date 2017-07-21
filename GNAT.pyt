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
# Version:     2.1.10                                                         #
# Revised:     2017-July-21                                                   #
# Released:                                                                   #
#                                                                             #
# License:     MIT License                                                    #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import arcpy
from os import path, makedirs
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
import CalculateGradient
import CalculateThreadedness

GNAT_version = "2.1.10"

strCatagoryStreamNetworkPreparation = "Main\\Step 1 - Stream Network Preparation"
strCatagoryStreamNetworkSegmentation = "Main\\Step 2 - Stream Network Segmentation"
strCatagoryGeomorphicAnalysis = "Main\\Step 3 - Geomorphic Attributes"
strCatagoryUtilities = "Utilities"
strCatagoryProjectManagement = "Project Management"

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
                      FindNetworkFeaturesTool,
                      NewGNATProject,
                      LoadNetworkToProject,
                      CommitRealization,
                      CalculateGradientTool,
                      CalculateThreadednessTool]


# GNAT Project Management
class NewGNATProject(object):
    """Define parameter definitions"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create a New GNAT Project"
        self.description = "Create a New GNAT Project."
        self.canRunInBackground = False
        self.category = strCatagoryProjectManagement

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Project Name",
            name="projectName",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Project Folder",
            name="projectFolder",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["File System"]

        paramBoolNewFolder = arcpy.Parameter(
            displayName="Create New Project Folder?",
            name="boolNewFolder",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="User Name (Operator)",
            name="metaOperator",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Region",
            name="metaRegion",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        param3.filter.list = ["CRB"]

        param4 = arcpy.Parameter(
            displayName="Watershed (HUC 8 Name)",
            name="metaWatershed",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        #TODO  add param4.filter.list = [], load and read from program.xml

        params = [param0,param1,paramBoolNewFolder,param2,param3,param4]
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

        return

    def execute(self, p, messages):
        """The source code of the tool."""
        from Riverscapes import Riverscapes

        arcpy.AddMessage(p[2].valueAsText)

        projectFolder = p[1].valueAsText

        if p[2].valueAsText == "true":
            projectFolder = path.join(p[1].valueAsText,p[0].valueAsText)
            makedirs(projectFolder)

        GNATProject = Riverscapes.Project()
        GNATProject.create(p[0].valueAsText,"GNAT",projectPath=projectFolder)
        GNATProject.addProjectMetadata("GNAT_Project_Version","0.1")
        GNATProject.addProjectMetadata("Operator",p[3].valueAsText)
        GNATProject.addProjectMetadata("Region",p[4].valueAsText)
        GNATProject.addProjectMetadata("Watershed",p[5].valueAsText)
        GNATProject.addProjectMetadata("GIS","Arc/ESRI")
        GNATProject.writeProjectXML()

        return


class LoadNetworkToProject(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Load Input Datsets"
        self.description = "Load Input Stream Network to GNAT Project. Tool Documentation: https://bitbucket.org/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/MovingWindow"
        self.canRunInBackground = False
        self.category = strCatagoryProjectManagement

    def getParameterInfo(self):
        """Define parameter definitions"""

        p1 = paramStreamNetwork

        paramNetworkTable = arcpy.Parameter(
            displayName="Network Table",
            name="tblNetwork",
            datatype="DETable",
            parameterType="Optional",
            direction="Input")

        params = [paramProjectXML,
                  p1,
                  paramNetworkTable]
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

        return

    def execute(self, p, messages):
        """The source code of the tool."""
        from Riverscapes import Riverscapes

        GNATProject = Riverscapes.Project(p[0].valueAsText)
        pathProject = GNATProject.projectPath

        # Create Project Paths if they do not exist
        pathInputs = pathProject + "\\Inputs"
        if not arcpy.Exists(pathInputs):
            makedirs(pathInputs)

        # KMW - The following is a lot of repeated code for each input. It contains file and folder creation and copying, rather than useing the project module to do this. This could be streamlined in the future, but
        # is working at the moment.
        if p[1].valueAsText: # Stream Network Input
            pathStreamNetworks = pathInputs + "\\StreamNetworks"
            nameStreamNetwork = arcpy.Describe(p[1].valueAsText).basename
            if not arcpy.Exists(pathStreamNetworks):
                makedirs(pathStreamNetworks)
            id_streamnetwork = Riverscapes.get_input_id(pathStreamNetworks, "StreamNetwork")
            pathStreamNetworkID = path.join(pathStreamNetworks, id_streamnetwork)
            makedirs(pathStreamNetworkID)
            arcpy.FeatureClassToFeatureClass_conversion(p[1].valueAsText, pathStreamNetworkID, nameStreamNetwork)
            GNATProject.addInputDataset(nameStreamNetwork,
                                        id_streamnetwork,
                                        path.join(path.relpath(pathStreamNetworkID, pathProject),
                                        nameStreamNetwork) + ".shp",
                                        p[1].valueAsText)

            if p[2].value:
                id_streamnetworkTable = Riverscapes.get_input_id(pathStreamNetworks, "StreamNetworkTable")
                extStreamNetworkTable = arcpy.Describe(p[2].valueAsText).extension
                nameStreamNetworkTable = arcpy.Describe(p[2].valueAsText).basename
                arcpy.TableToTable_conversion(p[2].valueAsText, pathStreamNetworkID, nameStreamNetworkTable)
                GNATProject.addInputDataset(nameStreamNetworkTable,
                                            id_streamnetworkTable,
                                            path.join(path.relpath(pathStreamNetworkID, pathProject),
                                            nameStreamNetworkTable) + "." + extStreamNetworkTable,
                                            p[2].valueAsText)

        # Write new XML
        GNATProject.writeProjectXML(p[0].valueAsText)

        return


class CommitRealization(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Commit Stream Network"
        self.description = "Commit Changes to the Stream Network as a new Realization in the GNAT Project."
        self.canRunInBackground = False
        self.category = strCatagoryProjectManagement
        return

    def getParameterInfo(self):
        """Define parameter definitions"""

        paramRealization = arcpy.Parameter(
            displayName="Realization Name",
            name="realization",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        paramIDField = arcpy.Parameter(
            displayName="Unique Reach ID Field",
            name="reachIDfield",
            datatype="Field",
            parameterType="Optional",
            direction="Input")

        paramNetworkTable = arcpy.Parameter(
            displayName="Network Table",
            name="tblNetwork",
            datatype="DETable",
            parameterType="Optional",
            direction="Input")

        params = [paramProjectXML, # 0
                  paramRealization,  # 1
                  paramStreamNetwork,  # 2
                  paramIDField,  # 3
                  paramNetworkTable]  # 4
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, p):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # if p[0].altered:
            # if p[0].value and arcpy.Exists(p[0].valueAsText):
            #     GNATProject = Riverscapes.Project(p[0].valueAsText)
                # GNATProject.loadProjectXML(p[0].valueAsText)

                # if p[1].altered:
                #     if p[1].value:
                #         #p[2].value = path.join(GNATProject.projectPath, "Outputs", p[1].valueAsText) + "\\GNAT_StreamNetwork.shp"
                #         pass
        # if p[2].altered:
            #if p[2].value and arcpy.Exists(p[2].valueAsText):
        populateFields(p[2],p[3],"")

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        from Riverscapes import Riverscapes

        if parameters[0].valueAsText:
            GNATProject = Riverscapes.Project(parameters[0].valueAsText)

            for realization in GNATProject.Realizations:
                if realization == parameters[1].valueAsText:
                    parameters[1].setErrorMessage("Realization " + parameters[1].valueAsText + " already exists.")
                    return

        return

    def execute(self, p, messages):
        """The source code of the tool."""
        from Riverscapes import Riverscapes

        # if in project mode, create workspaces as needed.
        if p[0].valueAsText:
            GNATProject = Riverscapes.Project(p[0].valueAsText)

            if p[1].valueAsText:
                outPath = path.join(GNATProject.projectPath, "Outputs",p[1].valueAsText)
                makedirs(outPath)

                outputGNATNetwork = path.join(outPath, "GNAT_StreamNetwork") + ".shp"
                outputNetworkTable = path.join(outPath , "GNAT_NetworkTable") + ".dbf"

                # todo if not idfield, then create one named NetID

                # Stream Network
                idRawStreamNetwork = GNATProject.get_dataset_id(p[2].valueAsText)

                arcpy.Copy_management(p[2].valueAsText,outputGNATNetwork)
                datasetGNATNetwork = Riverscapes.Dataset()
                datasetGNATNetwork.create("GNAT_StreamNetwork",
                                          path.relpath(outputGNATNetwork, GNATProject.projectPath))
                datasetGNATNetwork.id = p[1].valueAsText + "_GNAT_StreamNetwork"
                #datasetGNATNetwork.type = "GNAT_StreamNetwork"

                # Todo Get all fields as Meta for input or realization?

                # Network Table (Optional)
                idRawNetworkTable = None
                datasetGNATNetworkTable = None
                if p[4].value:
                    if arcpy.Exists(p[4].valueAsText):
                        idRawNetworkTable = GNATProject.get_dataset_id(p[3].valueAsText)

                        arcpy.Copy_management(p[4].valueAsText,outputNetworkTable)

                        datasetGNATNetworkTable = Riverscapes.Dataset()
                        datasetGNATNetworkTable.create("GNAT_NetworkTable",
                                                       path.relpath(outputNetworkTable, GNATProject.projectPath))
                        datasetGNATNetworkTable.type = "Table"
                        datasetGNATNetworkTable.id = p[1].valueAsText + "GNAT_NetworkTable"

                realization = Riverscapes.GNATRealization()
                realization.createGNATRealization(p[1].valueAsText,
                               idRawStreamNetwork,
                               datasetGNATNetwork,
                               idRawNetworkTable,
                               datasetGNATNetworkTable)
                realization.productVersion = str(GNAT_version)
                realization.parameters["FieldOriginalReachID"] = p[3].valueAsText

                GNATProject.addRealization(realization)
                GNATProject.writeProjectXML(p[0].valueAsText)

        return


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

        paramRealization = arcpy.Parameter(
            displayName="Realization Name",
            name="realization",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        paramRealization.enabled = "False"

        paramAnalysisName = arcpy.Parameter(
            displayName="Segmentation Name",
            name="analysisName",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        paramAnalysisName.enabled = "False"

        paramInStreamNetwork = arcpy.Parameter(
            displayName="Stream Network Polyline Feature Class",
            name="InputStreamNetwork",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")
        paramInStreamNetwork.filter.list = ["Polyline"]

        paramSegmentLength = arcpy.Parameter(
            displayName="Segment Length (Meters)",
            name="InputSegmentDistance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        paramSegmentLength.value = "200"

        paramDownstreamID = arcpy.Parameter(
            displayName="Downstream Reach ID",
            name="reachID",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")

        paramFieldStreamName = arcpy.Parameter(
            displayName="Stream Name Field",
            name="streamIndex",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        paramFieldStreamName.parameterDependencies = [paramInStreamNetwork.name]

        paramSegmentationMethod = arcpy.Parameter(
            displayName="Segmentation Method",
            name="strSegmentationMethod",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        paramSegmentationMethod.filter.list = Segmentation.listStrSegMethod

        paramBoolSplitAtConfluences = arcpy.Parameter(
            displayName="Split stream network at confluences before segmenting",
            name="boolNode",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        paramBoolRetainOrigAttributes = arcpy.Parameter(
            displayName="Retain Original attributes and geometry from input stream network",
            name="boolKeepOrig",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        # TODO if project mode, this is always yes.

        paramOutputSegmentedNetwork = arcpy.Parameter(
            displayName="Output Segmented Line Network",
            name="outputStreamOrderFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")

        return [paramProjectXML,
                paramRealization,
                paramAnalysisName,
                paramInStreamNetwork,
                paramSegmentLength,
                paramDownstreamID,
                paramFieldStreamName,
                paramSegmentationMethod,
                paramBoolSplitAtConfluences,
                paramBoolRetainOrigAttributes,
                paramOutputSegmentedNetwork]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, p):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        from Riverscapes import Riverscapes

        if p[0].value:
            if arcpy.Exists(p[0].valueAsText):
                GNATProject = Riverscapes.Project(p[0].valueAsText)

                p[1].enabled = "True"
                p[1].filter.list = GNATProject.Realizations.keys()
                p[10].enabled = "False"
                p[10].value = ""
                p[3].enabled = "False"

                if p[1].value:
                    currentRealization = GNATProject.Realizations.get(p[1].valueAsText)
                    p[3].value = currentRealization.GNAT_StreamNetwork.absolutePath(GNATProject.projectPath)
                    p[2].enabled = "True"
                    if p[2].value:
                        p[10].value = path.join(GNATProject.projectPath, "Outputs", p[1].valueAsText, "Analyses",
                                                p[2].valueAsText, "GNAT_SegmentedNetwork") + ".shp"

        else:
            p[1].filter.list = []
            p[1].value = ''
            p[1].enabled = "False"
            p[2].value = ""
            p[3].enabled = "True"
            p[10].enabled = "True"

        populateFields(p[3],p[6],"GNIS_Name")

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        # todo Check if analysis name already exists
        testProjected(parameters[3])

        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(Segmentation)
        from Riverscapes import Riverscapes

        output = p[10].valueAsText

        if p[0].value:
            GNATProject = Riverscapes.Project()
            GNATProject.loadProjectXML(p[0].valueAsText)
            if p[1].valueAsText:
                makedirs(path.join(GNATProject.projectPath, "Outputs", p[1].valueAsText, "Analyses",
                                   p[2].valueAsText))
                output = path.join(GNATProject.projectPath, "Outputs", p[1].valueAsText, "Analyses",
                                                p[2].valueAsText, "GNAT_SegmentedNetwork") + ".shp"


        Segmentation.main(p[3].valueAsText,
                          p[4].valueAsText,
                          p[5].valueAsText,
                          p[6].valueAsText,
                          p[7].valueAsText,
                          p[8].valueAsText,
                          p[9].valueAsText,
                          output)

        if p[0].value:
            if arcpy.Exists(p[0].valueAsText):
                GNATProject = Riverscapes.Project(p[0].valueAsText)

                outSegmentedNetwork = Riverscapes.Dataset()
                outSegmentedNetwork.create(arcpy.Describe(output).basename,
                                           path.relpath(path.join(output, "GNAT_SegmentedNetwork"),
                                                        GNATProject.projectPath) + ".shp",
                                           "GNAT_SegmentedNetwork")
                outSegmentedNetwork.id = p[1].valueAsText + "_" + p[2].valueAsText + "GNAT_SegmentedNetwork"

                realization = GNATProject.Realizations.get(p[1].valueAsText)
                realization.newAnalysisNetworkSegmentation(p[2].valueAsText,
                                                           p[4].valueAsText,
                                                           "NONE",
                                                           p[5].valueAsText,
                                                           p[6].valueAsText,
                                                           p[7].valueAsText,
                                                           p[8].valueAsText,
                                                           p[9].valueAsText,
                                                           outSegmentedNetwork)

                GNATProject.Realizations[p[1].valueAsText] = realization
                GNATProject.writeProjectXML()

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
            displayName="Output confluence node points",
            name="outputNodePointsFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param3.filter.list = ["Point"]

        param4 = arcpy.Parameter(
            displayName="Output junction points",
            name="outputJunctionPointsFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param4.filter.list = ["Point"]

        param5 = arcpy.Parameter(
            displayName="Scratch workspace",
            name="InputTempWorkspace",
            datatype="DEWorkspace", 
            parameterType="Optional",
            direction="Input")

        return [param0,param1,param2,param3,param4,param5]# + listControlParams

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
                         p[4].valueAsText)#,
                        # p[5].valueAsText)
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
        param3.enabled = False
        
        return [param0,param1,
                #param2,
                param3]

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
            p[1].valueAsText)
            #p[2].valueAsText,
            # getTempWorkspace(p[2].valueAsText))

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
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polygon"]

        param1 = arcpy.Parameter(
            displayName="Stream network polyline feature class",
            name="InputFCPolyline",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polyline"]

        param2 = arcpy.Parameter(
            displayName="Disaggregation step",
            name="InputDisaggregationStep",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param2.value = "5.0"

        param3 = arcpy.Parameter(
            displayName="Smoothing tolerance",
            name="InputSmoothing",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param3.value = "10.0"

        param4 = arcpy.Parameter(
            displayName="Output centerline feature class",
            name="OutputFCPolyline",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param4.filter.list = ["Polyline"]


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
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(Centerline)
        Centerline.main(p[0].valueAsText,
                                  p[1].valueAsText,
                                  p[2].valueAsText,
                                  p[3].valueAsText,
                                  p[4].valueAsText)

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


class CalculateGradientTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate Gradient"
        self.description = "Calculates gradient (percent rise/run) per stream reach feature."
        self.canRunInBackground = False
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Stream Network",
            name="InputStreamNetwork",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Elevation (DEM) Raster Dataset",
            name="InputDEM",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Output Shapefile",
            name="OutputStreamNetwork",
            datatype="DEShapefile",  # Integer
            parameterType="Required",
            direction="Output")

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
        reload(CalculateGradient)
        CalculateGradient.main(p[0].valueAsText,
                        p[1].valueAsText,
                        p[2].valueAsText)

        return


class CalculateThreadednessTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate Threadedness"
        self.description = "Calculates multi-threaded nodes per stream segment in a network."
        self.canRunInBackground = False
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input segmented stream network feature class",
            name="InputSegmentNetwork",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Input multi-threaded stream network feature class",
            name="InputFullNetwork",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polyline"]

        param2 = arcpy.Parameter(
            displayName="Output node feature class",
            name="OutputNodes",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Output")

        param3 = arcpy.Parameter(
            displayName="Output stream network feature class",
            name="OutputStreamNetwork",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Output")

        param4 = arcpy.Parameter(
            displayName="Scratch workspace",
            name="scratchWorkspace",
            datatype="DEWorkspace",
            parameterType="Required", # FIXME temporary fix;
            direction="Input")

        return [param0, param1, param2, param3, param4]

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
        reload(CalculateThreadedness)
        CalculateThreadedness.main(p[0].valueAsText,
                               p[1].valueAsText,
                               p[2].valueAsText,
                               p[3].valueAsText,
                               p[4].valueAsText)
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


def populateFields(parameterSource, parameterField, strDefaultFieldName):
    if parameterSource.value:
        if arcpy.Exists(parameterSource.valueAsText):
            # Get fields

            for field in arcpy.Describe(parameterSource.valueAsText).fields:
            # list_fields = []
            # for f in fields:
            #     list_fields.append(f.name)
                parameterField.filter.list.append(field.name)
            if strDefaultFieldName in parameterField.filter.list:#list_fields:
                parameterField.value = strDefaultFieldName
        else:
            parameterField.value = ""
            parameterField.filter.list = []
            parameterSource.setErrorMessage("Dataset does not exist.")

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

# Common Params
paramProjectXML = arcpy.Parameter(
    displayName="GNAT Project XML",
    name="projectXML",
    datatype="DEFile",
    parameterType="Optional",
    direction="Input")
paramProjectXML.filter.list = ["xml"]

paramStreamNetwork = arcpy.Parameter(
    displayName="Input Stream Network",
    name="InputFCStreamNetwork",
    datatype="DEFeatureClass",
    parameterType="Required",
    direction="Input")
paramStreamNetwork.filter.list = ["Polyline"]
