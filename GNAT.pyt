﻿# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
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
# Version:     2.6.2                                                          #
# Revised:     2018-Map-11                                                    #
# Released:    2018-April-25                                                  #
#                                                                             #
# License:     MIT License                                                    #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

import os
from os import path, makedirs
import arcpy
from tools import CalculateGradient, CalculateThreadedness, CombineAttributes, DividePolygonBySegment, \
    GenerateStreamOrder, GenerateNetworkAttributes, FindBraidedNetwork, FindSubnetworks, GenerateStreamBranches, \
    Sinuosity, Segmentation, TransferAttributesToLine, ValleyPlanform, moving_window
from tools.FCT import Centerline

GNAT_version = "2.6.2"

strCatagoryStreamNetworkPreparation = "Analyze Network Attributes\\Step 1 - Stream Network Preparation"
strCatagoryStreamNetworkSegmentation = "Analyze Network Attributes\\Step 2 - Stream Network Segmentation"
strCatagoryGeomorphicAnalysis = "Analyze Network Attributes\\Step 3 - Geomorphic Attributes"
strCatagoryProjectManagement = "Riverscapes Project Management"
strCatagoryUtilities = "Utilities"


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Geomorphic Network and Analysis Toolbox"
        self.alias = 'GNAT'
        self.description = "Tools for generating geomorphic attributes for a stream network."

        # List of tool classes associated with this toolbox
        self.tools = [FindSubnetworksTool,
                      GenerateNetworkAttributesTool,
                      GenerateStreamOrderTool,
                      StreamBranchesTool,
                      FindBraidedNetworkTool,
                      SinuosityAttributesTool,
                      SinuosityTool,
                      DividePolygonBySegmentsTool,
                      TransferLineAttributesTool,
                      FluvialCorridorCenterlineTool,
                      CombineAttributesTool,
                      SegmentationTool,
                      NewGNATProject,
                      LoadNetworkToProject,
                      CommitRealization,
                      CalculateGradientTool,
                      CalculateThreadednessTool,
                      MovingWindowSummaryTool]


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
        self.description = "Commit changes to the stream network as a new realization in a GNAT project."
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
        paramIDField.parameterDependencies = [paramStreamNetwork.name]

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

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
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


# Stream Network Prep Tools
class FindSubnetworksTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find Subnetworks"
        self.description = "Finds disconnected subnetworks within a stream network."
        self.canRunInBackground = False
        self.category = strCatagoryStreamNetworkPreparation

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input stream network shapefle",
            name="InputStreamNetwork",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Output shapefile",
            name="OutputStreamNetwork",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Output")

        param2 = arcpy.Parameter(
            displayName="Find topology errors",
            name="BoolError",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")


        return [param0, param1, param2]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, p):
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
        reload(FindSubnetworks)

        # testFType(p[0].valueAsText, 336)  # check to see if canals have been removed from input feature class
        FindSubnetworks.main(p[0].valueAsText,
                             p[1].valueAsText,
                             p[2].valueAsText)

        return


class GenerateNetworkAttributesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Generate Network Attributes"
        self.description = "Generates a series of network attributes, including edge type, node type, river kilometers," \
                           "and stream order."
        self.canRunInBackground = False
        self.category = strCatagoryStreamNetworkPreparation

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input stream network polyline feature class",
            name="InputStreamNetwork",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Primary stream name field (i.e. GNIS Name)",
            name="StreamNameField",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Output polyline feature class",
            name="OutputStreamNetwork",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Output")

        param3 = arcpy.Parameter(
            displayName="Calculate river kilometers",
            name="BoolRiverKM",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        return [param0, param1, param2, param3]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed. This method is called whenever a parameter
        has been changed."""

        if parameters[0].altered:
            fields = arcpy.ListFields(parameters[0].value)
            field_names = []
            for field in fields:
                field_names.append(field.name)
                if field.name == "GNIS_Name" or field.name == "GNIS_NAME" or field.name == "GNIS_name" or field.name == "gnis_name":
                    parameters[1].value = field.name
            parameters[1].filter.type = "ValueList"
            parameters[1].filter.list = field_names

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(GenerateNetworkAttributes)

        GenerateNetworkAttributes.main(p[0].valueAsText,
                                       p[1].valueAsText,
                                       p[2].valueAsText,
                                       p[3].valueAsText)
        return


class GenerateStreamOrderTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Generate Strahler Stream Order"
        self.description = "Generate Strahler stream order for the stream network"
        self.canRunInBackground = True
        self.category = strCatagoryStreamNetworkPreparation

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input stream network shapefile",
            name="InputStreamNetwork",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Primary stream name field (i.e. GNIS Name)",
            name="StreamNameField",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Output network shapefile with stream order",
            name="OutputStreamNetwork",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Output")
        param2.filter.list = ["Polyline"]

        param3 = arcpy.Parameter(
            displayName="Temporary workspace",
            name="TempWorkspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        param3.filter.list = ["Workspace"]

        return [param0, param1, param2, param3]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            fields = arcpy.ListFields(parameters[0].value)
            field_names = []
            for field in fields:
                field_names.append(field.name)
                if field.name == "GNIS_Name" or field.name == "GNIS_NAME" or field.name == "GNIS_name" or field.name == "gnis_name":
                    parameters[1].value = field.name
            parameters[1].filter.type = "ValueList"
            parameters[1].filter.list = field_names
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        testProjected(parameters[0])
        testMValues(parameters[0])
        return

    def execute(self, p, messages):
        """The source code of the tool."""

        reload(GenerateStreamOrder)

        GenerateStreamOrder.main(p[0].valueAsText,
                                 p[1].valueAsText,
                                 p[2].valueAsText,
                                 getTempWorkspace(p[3].valueAsText))


class StreamBranchesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Generate Stream Branches"
        self.description = "Generate stream branch IDs for the stream network."
        self.canRunInBackground = True
        self.category = strCatagoryStreamNetworkPreparation

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
            displayName="Input Stream Network Nodes",
            name="InputNetworknodes",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param1.filter.list = ["Point", "Multipoint"]

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

        return [param0, param1, param2, param3, param4, param5, param6]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            fields = arcpy.ListFields(parameters[0].value)
            field_names = []
            for field in fields:
                field_names.append(field.name)
                if field.name == "GNIS_Name":
                    parameters[2].value = field.name
                if field.name == "_strmordr_":
                    parameters[3].value = field.name
            parameters[2].filter.type = "ValueList"
            parameters[2].filter.list = field_names
            parameters[3].filter.type = "ValueList"
            parameters[3].filter.list = field_names

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

        paramInStreamNetwork = arcpy.Parameter(
            displayName="Stream network polyline feature class",
            name="InputStreamNetwork",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")
        paramInStreamNetwork.filter.list = ["Polyline"]

        paramSegmentLength = arcpy.Parameter(
            displayName="Segment length",
            name="InputSegmentDistance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        paramSegmentLength.value = "200"

        paramFieldStreamName = arcpy.Parameter(
            displayName="Stream name field",
            name="streamIndex",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        paramFieldStreamName.parameterDependencies = [paramInStreamNetwork.name]

        paramSegmentationMethod = arcpy.Parameter(
            displayName="Segmentation method",
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
            displayName="Retain original attributes and geometry from input stream network",
            name="boolKeepOrig",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        # TODO if project mode, this is always yes.

        paramOutputSegmentedNetwork = arcpy.Parameter(
            displayName="Output segmented line network",
            name="outputStreamOrderFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")

        return [paramInStreamNetwork, #p[0]
                paramSegmentLength, #p[1]
                paramFieldStreamName, #p[3] -> 2
                paramSegmentationMethod, #p[4] -> 3
                paramBoolSplitAtConfluences, #p[5] -> 4
                paramBoolRetainOrigAttributes, #p[6] -> 5
                paramOutputSegmentedNetwork, #p[7] -> 6
                paramProjectXML, #p[8] -> 7
                paramRealization, #p[9] -> 8
                paramSegmentAnalysisName] #p[10] -> 9


    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, p):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        from Riverscapes import Riverscapes

        if p[7].value:
            if arcpy.Exists(p[7].valueAsText):
                GNATProject = Riverscapes.Project(p[7].valueAsText)

                p[8].enabled = "True"
                p[8].filter.list = GNATProject.Realizations.keys()
                p[6].enabled = "False"

                if p[8].value:
                    currentRealization = GNATProject.Realizations.get(p[8].valueAsText)
                    p[0].value = currentRealization.GNAT_StreamNetwork.absolutePath(GNATProject.projectPath)
                    p[9].enabled = "True"
                    if p[9].value:
                        p[6].value = path.join(GNATProject.projectPath, "Outputs", p[8].valueAsText, "Analyses",
                                                p[9].valueAsText, "SegmentedNetwork") + ".shp"

        else:
            p[8].filter.list = []
            p[8].value = ''
            p[8].enabled = "False"
            p[9].value = ""
            p[6].enabled = "True"

        populateFields(p[0],p[2],"GNIS_Name")

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        # todo Check if analysis name already exists
        testProjected(parameters[0])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(Segmentation)
        from Riverscapes import Riverscapes

        output = p[6].valueAsText

        # Where the tool outputs will be store for Riverscapes projects
        if p[7].value:
            GNATProject = Riverscapes.Project()
            GNATProject.loadProjectXML(p[7].valueAsText)
            if p[8].valueAsText:
                makedirs(path.join(GNATProject.projectPath, "Outputs", p[8].valueAsText, "Analyses",
                                   p[9].valueAsText))
                output = path.join(GNATProject.projectPath, "Outputs", p[8].valueAsText, "Analyses",
                                                p[9].valueAsText, "SegmentedNetwork") + ".shp"

        # Main tool module
        Segmentation.main(p[0].valueAsText,
                          p[1].valueAsText,
                          p[2].valueAsText,
                          p[3].valueAsText,
                          p[4].valueAsText,
                          p[5].valueAsText,
                          output)


        # Add tool run to the Riverscapes project XML
        if p[7].value:
            if arcpy.Exists(p[7].valueAsText):

                GNATProject = Riverscapes.Project(p[7].valueAsText)

                outSegmentedNetwork = Riverscapes.Dataset()
                outSegmentedNetwork.create(arcpy.Describe(output).basename,
                                           path.join("Outputs", str(p[8].value), "Analyses", str(p[9].value),
                                                     arcpy.Describe(output).basename + ".shp"),
                                           "SegmentedNetwork")
                outSegmentedNetwork.id = "SegmentedNetwork"

                realization = GNATProject.Realizations.get(p[8].valueAsText)
                realization.newAnalysisNetworkSegmentation(p[9].valueAsText,
                                                           p[1].valueAsText,
                                                           "NONE",
                                                           p[2].valueAsText,
                                                           p[3].valueAsText,
                                                           p[4].valueAsText,
                                                           p[5].valueAsText,
                                                           p[6].valueAsText,
                                                           outSegmentedNetwork)

                GNATProject.Realizations[p[8].valueAsText] = realization
                GNATProject.writeProjectXML()

        return

class MovingWindowSummaryTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Moving Window Summary"
        self.description = "Generate Moving Window Segment for a stream network."
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""

        paramInStreamNetwork = arcpy.Parameter(
            displayName="Stream network polyline feature class",
            name="InputStreamNetwork",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")
        paramInStreamNetwork.filter.list = ["Polyline"]

        paramFieldStreamName = arcpy.Parameter(
            displayName="Stream name or Branch field",
            name="streamIndex",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        paramFieldStreamName.parameterDependencies = [paramInStreamNetwork.name]

        param_seeddistance = arcpy.Parameter(
            displayName="Seed Point Distance",
            name="InputSegmentDistance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_seeddistance.value = "200"

        param_windowsizes = arcpy.Parameter(
            displayName="Window Sizes",
            name="InputWindowSizes",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        param_stat_fields = arcpy.Parameter(
            displayName="Calculate Statistics on Field(s)",
            name="statfields",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        # param_stat_fields.filter.list = ['Text']
        # param_stat_fields.parameterDependencies = [paramInStreamNetwork.name]

        paramOutputSegmentedNetwork = arcpy.Parameter(
            displayName="Output Moving Windows",
            name="outputStreamOrderFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")

        paramOutputSeedPoints = arcpy.Parameter(
            displayName="Output Seed Points",
            name="outputSeedPointFC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")

        return [paramInStreamNetwork,  # p[0]
                paramFieldStreamName,  # p[1]
                param_seeddistance,  # p[2]
                param_windowsizes,  # p[3]
                param_stat_fields,  # p[4]
                paramOutputSegmentedNetwork,  # p[5]
                paramOutputSeedPoints,  # p[6]
                paramProjectXML,  # p[7]
                paramRealization,  # p[8]
                paramSegmentAnalysisName,  # p[9]
                paramTempWorkspace]  # p[10]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, p):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        from Riverscapes import Riverscapes

        if p[7].value:
            if arcpy.Exists(p[7].valueAsText):
                GNATProject = Riverscapes.Project(p[7].valueAsText)

                p[8].enabled = "True"
                p[8].filter.list = GNATProject.Realizations.keys()
                p[5].enabled = "False"
                p[6].enabled = "False"

                if p[8].value:
                    currentRealization = GNATProject.Realizations.get(p[8].valueAsText)
                    #p[0].value = currentRealization.GNAT_StreamNetwork.absolutePath(GNATProject.projectPath)
                    p[9].enabled = "True"
                    if p[9].value:
                        p[5].value = path.join(GNATProject.projectPath, "Outputs", p[8].valueAsText, "Analyses",
                                                p[9].valueAsText, "MovingWindows") + ".shp"
                        p[6].value = path.join(GNATProject.projectPath, "Outputs", p[8].valueAsText, "Analyses",
                               p[9].valueAsText, "SeedPoints") + ".shp"
        else:
            p[8].filter.list = []
            p[8].value = ''
            p[8].enabled = "False"
            p[9].value = ""
            p[5].enabled = "True"
            p[6].enabled = "True"

        populateFields(p[0], p[1], "GNIS_Name")
        p[4].filter.list = [f.name for f in arcpy.Describe(p[0].value).fields if f.type in ["Single", "Double", "Integer", "SmallInteger"]] if p[0].value else []
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        # todo Check if analysis name already exists
        testProjected(parameters[0])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(moving_window)
        from Riverscapes import Riverscapes

        inputLines = p[0].valueAsText
        fieldStreamRoute = p[1].valueAsText
        seed_dist = int(p[2].valueAsText)
        window_sizes = [float(ws) for ws in p[3].valueAsText.split(";")]
        stat_fields = p[4].valueAsText.split(";")

        outputWindows = p[5].valueAsText
        outputSeedPoints = p[6].valueAsText

        # Where the tool outputs will be store for Riverscapes projects
        if p[7].value:
            GNATProject = Riverscapes.Project()
            GNATProject.loadProjectXML(p[7].valueAsText)
            if p[8].valueAsText:
                makedirs(path.join(GNATProject.projectPath, "Outputs", p[8].valueAsText, "Analyses",
                                   p[9].valueAsText))
                outputWindows = path.join(GNATProject.projectPath, "Outputs", p[8].valueAsText, "Analyses",
                                                p[9].valueAsText, "MovingWindows") + ".shp"
                outputSeedPoints = path.join(GNATProject.projectPath, "Outputs", p[8].valueAsText, "Analyses",
                                                p[9].valueAsText, "SegmentedNetwork") + ".shp"

        # Main tool module
        moving_window.main(inputLines,
                           fieldStreamRoute,
                           seed_dist,
                           window_sizes,
                           stat_fields,
                           outputWindows,
                           outputSeedPoints,
                           getTempWorkspace(p[10].valueAsText))

        # Add tool run to the Riverscapes project XML
        if p[7].value:
            if arcpy.Exists(p[7].valueAsText):

                GNATProject = Riverscapes.Project(p[7].valueAsText)

                outSegmentedNetwork = Riverscapes.Dataset()
                outSegmentedNetwork.create(arcpy.Describe(outputWindows).basename,
                                           path.join("Outputs", str(p[8].value), "Analyses", str(p[9].value),
                                                     arcpy.Describe(outputWindows).basename + ".shp"),
                                           "SegmentedNetwork")
                outSegmentedNetwork.id = "SegmentedNetwork"

                realization = GNATProject.Realizations.get(p[8].valueAsText)
                realization.newAnalysisNetworkSegmentation(p[9].valueAsText,
                                                           p[1].valueAsText,
                                                           "NONE",
                                                           p[2].valueAsText,
                                                           p[3].valueAsText,
                                                           p[4].valueAsText,
                                                           p[5].valueAsText,
                                                           p[6].valueAsText,
                                                           outSegmentedNetwork)

                GNATProject.Realizations[p[8].valueAsText] = realization
                GNATProject.writeProjectXML()

        return
# Geomorphic Attributes Tools
class CalculateGradientTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate Gradient"
        self.description = "Calculates gradient (percent rise/run) per stream reach feature."
        self.canRunInBackground = False
        self.category = strCatagoryGeomorphicAnalysis

    def getParameterInfo(self):
        """Define parameter definitions"""
        paramElevationRaster = arcpy.Parameter(
            displayName="Elevation (DEM) Raster Dataset",
            name="InputDEM",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Input")

        return [paramStreamNetwork,
                paramElevationRaster,
                paramRiverscapesBool,
                paramProjectXML,
                paramRealization,
                paramSegmentAnalysisName,
                paramAttributeAnalysisName]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, p):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Tool input variables
        inSegmentedStreamNetwork = p[0]

        # Riverscape project variables
        paramRiverscapesBool = p[2]
        paramProjectXML = p[3]
        paramRealization = p[4]
        paramSegmentAnalysis = p[5]
        paramAttributeAnalysis = p[6]

        if paramRiverscapesBool.value == True:
            paramProjectXML.enabled = True
            if paramProjectXML.value:
                from Riverscapes import Riverscapes
                if arcpy.Exists(paramProjectXML.valueAsText):
                    GNATProject = Riverscapes.Project(str(paramProjectXML.value))

                    paramRealization.enabled = True
                    paramRealization.filter.list = GNATProject.Realizations.keys()

                    if paramRealization.value:
                        currentRealization = GNATProject.Realizations.get(str(paramRealization.value))
                        paramSegmentAnalysis.enabled = True
                        paramSegmentAnalysis.filter.list = currentRealization.analyses.keys()
                        paramAttributeAnalysis.enabled = True

                        if paramSegmentAnalysis.value:
                            # Switches input stream network feature class to realization segmented network feature class.
                            currentAnalysis = currentRealization.analyses.get(paramSegmentAnalysis.value)
                            segmentedOutput = currentAnalysis.outputDatasets["SegmentedNetwork"]
                            inSegmentedStreamNetwork.value = segmentedOutput.absolutePath(GNATProject.projectPath)

        else:
            paramProjectXML.value = ""
            paramProjectXML.enabled = False
            paramRealization.value = ""
            paramRealization.enabled = False
            paramSegmentAnalysis.value = ""
            paramSegmentAnalysis.enabled = False
            paramAttributeAnalysis.value = ""
            paramAttributeAnalysis.enabled = False

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        # todo Check if analysis name already exists
        testProjected(parameters[0])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(CalculateGradient)
        setEnvironmentSettings()

        # Tool input variables
        inSegmentedStreamNetwork = p[0].valueAsText
        inDEM = p[1].valueAsText

        # Riverscapes project variables
        paramRiverscapesBool = p[2]
        paramProjectXML = p[3].valueAsText
        paramRealization = p[4].valueAsText
        paramSegmentAnalysis = p[5].valueAsText
        paramAttributeAnalysis = p[6].valueAsText

        # Where the tool output data will be stored in the Riverscapes Project directory
        if paramRiverscapesBool.value == True:
            if paramProjectXML:
                from Riverscapes import Riverscapes
                GNATProject = Riverscapes.Project()
                GNATProject.loadProjectXML(paramProjectXML)

                # Where to store attribute analyses input/output datasets
                if paramSegmentAnalysis:
                    attributesDir = path.join(GNATProject.projectPath, "Outputs",
                                              paramRealization, "Analyses",
                                              paramSegmentAnalysis,
                                              "GeomorphicAttributes", paramAttributeAnalysis)
                    if not os.path.exists(attributesDir):
                        makedirs(attributesDir)
                    if not os.path.exists(os.path.join(attributesDir, "Inputs")):
                        makedirs(os.path.join(attributesDir, "Inputs"))
                    if not os.path.exists(os.path.join(attributesDir, "Outputs")):
                        makedirs(os.path.join(attributesDir, "Outputs"))

        # Main tool module
        CalculateGradient.main(inSegmentedStreamNetwork, inDEM)

        # Add tool run to the Riverscapes project XML
        if paramRiverscapesBool.value == True:
            if paramProjectXML:
                from Riverscapes import Riverscapes
                if arcpy.Exists(paramProjectXML):

                    inDemDS = Riverscapes.Dataset()
                    inDemDS.create(os.path.basename(inDEM),
                                   os.path.join(attributesDir, "Inputs",
                                    os.path.basename(inDEM)))
                    inDemDS.id = "InputDEM"

                    GNATProject = Riverscapes.Project(paramProjectXML)

                    realization = GNATProject.Realizations.get(paramRealization)
                    analysis = realization.analyses.get(paramSegmentAnalysis)
                    analysis.newAnalysisGradient(paramAttributeAnalysis,
                                                 "Gradient",
                                                inDemDS,
                                                "SegmentedNetwork")

                    realization.analyses[paramSegmentAnalysis] = analysis
                    GNATProject.Realizations[paramRealization] = realization
                    GNATProject.writeProjectXML()

                    # Inform user about where sinuosity/planform attributes were added
                    GNAT_StreamNetwork_path = realization.GNAT_StreamNetwork.absolutePath(
                        GNATProject.projectPath)
                    arcpy.AddMessage("{0} {1}".format("Gradient attribute added to",
                                                      GNAT_StreamNetwork_path))
        return


class CalculateThreadednessTool(object):
        def __init__(self):
            """Define the tool (tool name is the name of the class)."""
            self.label = "Calculate Threadedness"
            self.description = "Calculates multi-threaded nodes per stream segment in a network."
            self.canRunInBackground = False
            self.category = strCatagoryGeomorphicAnalysis

        def getParameterInfo(self):
            """Define parameter definitions"""
            param0 = arcpy.Parameter(
                displayName="Input segmented stream network feature class",
                name="InputSegmentNetwork",
                datatype="DEShapefile",
                parameterType="Required",
                direction="Input")
            param0.filter.list = ["Polyline"]

            param1= arcpy.Parameter(
                displayName="Input attributed stream network feature class",
                name="InputFullNetwork",
                datatype="DEShapefile",
                parameterType="Required",
                direction="Input")
            param1.filter.list = ["Polyline"]

            param2 = arcpy.Parameter(
                displayName="Scratch workspace",
                name="scratchWorkspace",
                datatype="DEWorkspace",
                parameterType="Required",  # FIXME temporary fix
                direction="Input")

            return [param0,
                    param1,
                    param2,
                    paramRiverscapesBool, # 4 -> 3
                    paramProjectXML, # 5 -> 4
                    paramRealization, # 6 -> 5
                    paramSegmentAnalysisName, # 7 -> 6
                    paramAttributeAnalysisName] # 8 -> 7

        def isLicensed(self):
            """Set whether tool is licensed to execute."""
            return True

        def updateParameters(self, p):
            """Modify the values and properties of parameters before internal
            validation is performed.  This method is called whenever a parameter
            has been changed."""

            # Tool input variables
            inSegmentedStreamNetwork = p[0]

            # Riverscapes project variables
            paramRiverscapesBool = p[3]
            paramProjectXML = p[4]
            paramRealization = p[5]
            paramSegmentAnalysis = p[6]
            paramAttributeAnalysis = p[7]

            if paramRiverscapesBool.value == True:
                paramProjectXML.enabled = True
                if paramProjectXML.value:
                    from Riverscapes import Riverscapes
                    if arcpy.Exists(paramProjectXML.value):
                        GNATProject = Riverscapes.Project(paramProjectXML.valueAsText)

                        paramRealization.enabled = "True"
                        paramRealization.filter.list = GNATProject.Realizations.keys()

                        if paramRealization.value:
                            currentRealization = GNATProject.Realizations.get(str(paramRealization.value))
                            paramSegmentAnalysis.enabled = True
                            paramSegmentAnalysis.filter.list = currentRealization.analyses.keys()
                            paramAttributeAnalysis.enabled = True

                            if paramSegmentAnalysis.value:
                                # Switches input stream network feature class to realization segmented network feature class.
                                currentAnalysis = currentRealization.analyses.get(paramSegmentAnalysis.value)
                                segmentedOutput = currentAnalysis.outputDatasets["SegmentedNetwork"]
                                inSegmentedStreamNetwork.value = segmentedOutput.absolutePath(GNATProject.projectPath)
            else:
                paramProjectXML.value = ""
                paramProjectXML.enabled = False
                paramRealization.value = ""
                paramRealization.enabled = False
                paramSegmentAnalysis.value = ""
                paramSegmentAnalysis.enabled = False
                paramAttributeAnalysis.value = ""
                paramAttributeAnalysis.enabled = False

            return

        def updateMessages(self, parameters):
            """Modify the messages created by internal validation for each tool
            parameter. This method is called after internal validation."""
            testProjected(parameters[0])
            return

        def execute(self, p, messages):
            """The source code of the tool."""
            reload(CalculateThreadedness)
            setEnvironmentSettings()

            # Tool input variables
            inSegmentedStreamNetwork = p[0].valueAsText
            inFullThreadNetwork = p[1].valueAsText
            scratchWorkspace = p[2].valueAsText

            # Riverscapes project variables
            paramRiverscapesBool = p[3]
            paramProjectXML = p[4].valueAsText
            paramRealization = p[5].valueAsText
            paramSegmentAnalysis = p[6].valueAsText
            paramAttributeAnalysis = p[7].valueAsText

            # Where the tool output data will be stored
            if paramRiverscapesBool.value == True:
                if paramProjectXML:
                    from Riverscapes import Riverscapes
                    GNATProject = Riverscapes.Project()
                    GNATProject.loadProjectXML(paramProjectXML)

                    # Where to store attribute analyses input/output datasets
                    if paramSegmentAnalysis:
                        attributesDir = path.join(GNATProject.projectPath, "Outputs",
                                                  paramRealization, "Analyses",
                                                  paramSegmentAnalysis,
                                                  "GeomorphicAttributes", paramAttributeAnalysis)
                        if not os.path.exists(attributesDir):
                            makedirs(attributesDir)
                        if not os.path.exists(os.path.join(attributesDir, "Inputs")):
                            makedirs(os.path.join(attributesDir, "Inputs"))
                        if not os.path.exists(os.path.join(attributesDir, "Outputs")):
                            makedirs(os.path.join(attributesDir, "Outputs"))

            # Main tool module
            CalculateThreadedness.main(inSegmentedStreamNetwork,
                                       inFullThreadNetwork,
                                       scratchWorkspace)

            # Add results of tool processing to the Riverscapes project XML
            if paramRiverscapesBool.value == True:
                if paramProjectXML:
                    from Riverscapes import Riverscapes
                    if arcpy.Exists(paramProjectXML):
                        relativeDir = os.path.join("Outputs", paramRealization, "Analyses", paramSegmentAnalysis,
                                                   "GeomorphicAttributes", paramAttributeAnalysis)

                        inThreadedNetworkDS = Riverscapes.Dataset()
                        inThreadedNetworkDS.create(os.path.basename(inFullThreadNetwork),
                                                os.path.join(relativeDir, "Inputs",
                                                os.path.basename(inFullThreadNetwork)))
                        inThreadedNetworkDS.id = "InputThreadedNetwork"

                        GNATProject = Riverscapes.Project(paramProjectXML)

                        realization = GNATProject.Realizations.get(paramRealization)
                        analysis = realization.analyses.get(paramSegmentAnalysis)
                        analysis.newAnalysisThreadedness(paramAttributeAnalysis,
                                                         "NODES_BM",
                                                         "NODES_BB",
                                                         "NODES_TC",
                                                         inThreadedNetworkDS,
                                                         "SegmentNetwork")

                        realization.analyses[paramSegmentAnalysis] = analysis
                        GNATProject.Realizations[paramRealization] = realization
                        GNATProject.writeProjectXML()

                        # Inform user about where sinuosity/planform attributes were added
                        GNAT_StreamNetwork_path = realization.GNAT_StreamNetwork.absolutePath(
                            GNATProject.projectPath)
                        arcpy.AddMessage("{0} {1}".format("Threadedness attributes added to",
                                                          GNAT_StreamNetwork_path))
            return


class SinuosityAttributesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate Sinuosity Attributes"
        self.description = "Calculates Channel, Planform and Valley Bottom Sinuosity Attributes."
        self.canRunInBackground = True
        self.category = strCatagoryGeomorphicAnalysis

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Segmented Stream Network",
            name="InputFCChannelSinuosity",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Input Valley Centerline",
            name="InputFCValleyCenterline",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polyline"]

        param2 = arcpy.Parameter(
            displayName="Segment ID Field",
            name="FieldsegmentID",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param2.parameterDependencies = [param0.name]

        paramFieldFilter = arcpy.Parameter(
            displayName="Segment Filter Field",
            name="FieldFilter",
            datatype="Field",
            parameterType="Optional",
            direction="Input")

        return [param0,
                param1,
                param2,
                paramTempWorkspace,
                paramFieldFilter,
                paramProjectXML,  # 5
                paramRealization,  # 6
                paramSegmentAnalysisName,  # 7
                paramAttributeAnalysisName]  # 8

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, p):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Riverscape project parameters
        paramProjectXML = p[5]
        paramRealization = p[6]
        paramSegmentAnalysis = p[7]
        paramAttributeAnalysis = p[8]

        populateFields(p[0], p[4], None)

        if paramProjectXML.value:
            from Riverscapes import Riverscapes
            if arcpy.Exists(paramProjectXML.valueAsText):
                p[0].enabled = False
                GNATProject = Riverscapes.Project(str(paramProjectXML.value))
                paramRealization.enabled = True
                paramRealization.filter.list = GNATProject.Realizations.keys()
                if paramRealization.value:
                    currentRealization = GNATProject.Realizations.get(str(paramRealization.value))
                    paramSegmentAnalysis.enabled = True
                    paramSegmentAnalysis.filter.list = currentRealization.analyses.keys()
                    paramAttributeAnalysis.enabled = True
                    if paramSegmentAnalysis.value:
                        # Switches input stream network feature class to realization segmented network feature class.
                        currentAnalysis = currentRealization.analyses.get(paramSegmentAnalysis.value)
                        segmentedOutput = currentAnalysis.outputDatasets["SegmentedNetwork"]
                        p[0].value = segmentedOutput.absolutePath(GNATProject.projectPath)

        else:
            paramRealization.value = ""
            paramRealization.enabled = False
            paramSegmentAnalysis.value = ""
            paramSegmentAnalysis.enabled = False
            paramAttributeAnalysis.value = ""
            paramAttributeAnalysis.enabled = False
            # p[0].value = ""
            # p[0].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(ValleyPlanform)
        setEnvironmentSettings()

        # Tool input variables
        inChannelSinuosity = p[0].valueAsText
        inValleyCenterline = p[1].valueAsText

        # Riverscapes project variables
        fieldFilter = p[4].valueAsText
        paramProjectXML = p[5].valueAsText
        paramRealization = p[6].valueAsText
        paramSegmentAnalysis = p[7].valueAsText
        paramAttributeAnalysis = p[8].valueAsText

        # Where the tool output data will be stored in Riverscapes Project directory
        if paramProjectXML and arcpy.Exists(paramProjectXML):
            from Riverscapes import Riverscapes
            GNATProject = Riverscapes.Project()
            GNATProject.loadProjectXML(paramProjectXML)

            project_centerlines = [cl for cl in GNATProject.InputDatasets.itervalues() if cl.type == "VB_Centerline"]

            #if any(inValleyCenterline in [cl])

        # Execute Tool
        ValleyPlanform.main(inChannelSinuosity,
                            inValleyCenterline,
                            getTempWorkspace(p[3].valueAsText),
                            filterfield=p[4].valueAsText,
                            field_segid=p[2].valueAsText)

        # Add results of tool processing to the Riverscapes project XML
        if paramProjectXML and arcpy.Exists(paramProjectXML):
            from Riverscapes import Riverscapes
            # Riverscapes requires relative file paths
            relativeDir = os.path.join("Outputs", paramRealization, "Analyses", paramSegmentAnalysis,
                                       "GeomorphicAttributes", paramAttributeAnalysis)

            inValleyCenterlineDS = Riverscapes.Dataset()
            inValleyCenterlineDS.create(os.path.basename(inValleyCenterline),
                                        os.path.join(relativeDir, "Inputs", os.path.basename(inValleyCenterline)))
            inValleyCenterlineDS.id = "InputValleyCenterline"

            GNATProject = Riverscapes.Project(paramProjectXML)
            realization = GNATProject.Realizations.get(paramRealization)
            analysis = realization.analyses.get(paramSegmentAnalysis)
            analysis.newAnalysisSinuosityAttributes(paramAttributeAnalysis,
                                                    inValleyCenterlineDS,
                                                    "Sin_Chan",
                                                    "Sin_Plan",
                                                    "Sin_VB",
                                                    ValleyPlanform.__version__)
            realization.analyses[paramSegmentAnalysis] = analysis
            GNATProject.Realizations[paramRealization] = realization
            GNATProject.writeProjectXML()

        return


# Utilities
class SinuosityTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Sinuosity (simple)"
        self.description = "Calculate Sinuosity for a polyline feature class"
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""

        param00 = arcpy.Parameter(
            displayName="Type of Sinuosity",
            name="SinuosityType",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param00.filter.list = ["Polyline"]

        param0 = arcpy.Parameter(
            displayName="Input segmented stream network polyline feature class",
            name="InputFCCenterline",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Output stream network feature class",
            name="OutputFCNetwork",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output")

        return [param0,
		param1,
                paramRiverscapesBool, #2
                paramProjectXML, #3
                paramRealization, #4
                paramSegmentAnalysisName, #5
                paramAttributeAnalysisName] #6

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, p):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        inSegmentedStreamNetwork = p[0]
	outputFCNetwork = p[1]

        paramRiverscapesBool = p[2]
        paramProjectXML = p[3]
        paramRealization = p[4]
        paramSegmentAnalysis = p[5]
        paramAttributeAnalysis = p[6]

        if paramRiverscapesBool.value == True:
            paramProjectXML.enabled = True
            if paramProjectXML.value:
                from Riverscapes import Riverscapes
                if arcpy.Exists(paramProjectXML.valueAsText):
                    GNATProject = Riverscapes.Project(paramProjectXML.valueAsText)

                    paramRealization.enabled = True
                    paramRealization.filter.list = GNATProject.Realizations.keys()

                    if paramRealization.value:
                        currentRealization = GNATProject.Realizations.get(paramRealization.valueAsText)

                        paramSegmentAnalysis.enabled = True
                        paramSegmentAnalysis.filter.list = currentRealization.analyses.keys()
                        paramAttributeAnalysis.enabled = True

                        if paramSegmentAnalysis.value:
                            # Switches input stream network feature class to realization segmented network feature class.
                            currentAnalysis = currentRealization.analyses.get(paramSegmentAnalysis.value)
                            segmentedOutput = currentAnalysis.outputDatasets["SegmentedNetwork"]
                            inSegmentedStreamNetwork.value = segmentedOutput.absolutePath(GNATProject.projectPath)

        else:
            paramProjectXML.value = ""
            paramProjectXML.enabled = False
            paramRealization.value = ""
            paramRealization.enabled = False
            paramSegmentAnalysis.value = ""
            paramSegmentAnalysis.enabled = False
            paramAttributeAnalysis.value = ""
            paramAttributeAnalysis.enabled = False

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(Sinuosity)
        setEnvironmentSettings()

        # Tool input variables
        inCenterline = p[0].valueAsText
	outputNetwork = p[1].valueAsText

        # Riverscapes project variables
        paramRiverscapesBool = p[2]
        paramProjectXML = p[3].valueAsText
        paramRealization = p[4].valueAsText
        paramSegmentAnalysis = p[5].valueAsText
        paramAttributeAnalysis = p[6].valueAsText

        # outSinuosityName = os.path.basename(outSinuosity)
        paramChannelSinuosityField = "Sinuosity"

        # Where the tool output data will be stored in Riverscapes Project directory
        if paramRiverscapesBool.value == True:
            if paramProjectXML:
                from Riverscapes import Riverscapes
                GNATProject = Riverscapes.Project()
                GNATProject.loadProjectXML(paramProjectXML)

                # Where to store attribute analyses input/output datasets
                if paramSegmentAnalysis:
                    attributesDir = path.join(GNATProject.projectPath, "Outputs",
                                              paramRealization, "Analyses",
                                              paramSegmentAnalysis,
                                              "GeomorphicAttributes", paramAttributeAnalysis)
                    if not os.path.exists(attributesDir):
                        makedirs(attributesDir)
                    if not os.path.exists(os.path.join(attributesDir, "Inputs")):
                        makedirs(os.path.join(attributesDir, "Inputs"))
                    if not os.path.exists(os.path.join(attributesDir, "Outputs")):
                        makedirs(os.path.join(attributesDir, "Outputs"))

        # Main tool module
        Sinuosity.main(inCenterline, outputNetwork, paramChannelSinuosityField)

        # Add results of tool processing to the Riverscapes project XML
        if paramRiverscapesBool.value == True:
            if paramProjectXML:
                from Riverscapes import Riverscapes
                if arcpy.Exists(paramProjectXML):
                    GNATProject = Riverscapes.Project(paramProjectXML)

                    realization = GNATProject.Realizations.get(paramRealization)
                    analysis = realization.analyses.get(paramSegmentAnalysis)
                    analysis.newAnalysisSinuosity(paramAttributeAnalysis,
                                                  paramChannelSinuosityField,
                                                  "SegmentedNetwork")

                    realization.analyses[paramSegmentAnalysis] = analysis
                    GNATProject.Realizations[paramRealization] = realization
                    GNATProject.writeProjectXML()

                    # Inform user about where sinuosity/planform attributes were added
                    GNAT_StreamNetwork_path = realization.GNAT_StreamNetwork.absolutePath(
                        GNATProject.projectPath)
                    arcpy.AddMessage("{0}{1}".format("Sinuosity attribute added to ",
                                                      GNAT_StreamNetwork_path))

        return


class FindBraidedNetworkTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find Braids In Stream Network"
        self.description = "Find braided segments in a stream network."
        self.canRunInBackground = True
        self.category = strCatagoryUtilities

    def getParameterInfo(self):
        """Define parameter definitions"""
        return [paramStreamNetwork]

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
            displayName="Search distance",
            name="SearchDistance",
            datatype="Double",
            parameterType="Optional",
            direction="Input")
        param3.value = 50

        param4 = arcpy.Parameter(
            displayName="Scratch workspace",
            name="scratchWorkspace",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input")
        param4.filter.list = ["Local Database"]

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
        testProjected(parameters[0])
        testProjected(parameters[1])
        testWorkspacePath(parameters[4])
        return

    def execute(self, p, messages):
        """The source code of the tool."""
        reload(TransferAttributesToLine)
        setEnvironmentSettings()

        TransferAttributesToLine.main(p[0].valueAsText,
                                      p[1].valueAsText,
                                      p[2].valueAsText,
                                      p[3].value,
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

        return [param0, param1, param2, param3]

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


# Other Functions #
def setEnvironmentSettings():
    arcpy.env.OutputMFlag = "Disabled"
    arcpy.env.OutputZFlag = "Disabled"
    return


def getTempWorkspace(strWorkspaceParameter):
    return "in_memory" if strWorkspaceParameter in [None, ""] else strWorkspaceParameter


def testProjected(parameter):
    if parameter.value:
        if arcpy.Exists(parameter.value):
            if arcpy.Describe(parameter.value).spatialReference.type <> u"Projected":
                parameter.setErrorMessage("Input " + parameter.name + " must be in a projected coordinate system.")
                return False
            else:
                return True


def testMValues(parameter):
    if parameter.value:
        if arcpy.Exists(parameter.value):
            if arcpy.Describe(parameter.value).hasM is True:
                parameter.setErrorMessage("Input " + parameter.name + " must not be M-enabled. Make sure to disable M-values in the Environment Settings for this tool.")
                return False
            else:
                return True


def populateFields(parameterSource, parameterField, strDefaultFieldName=None):
    if parameterSource.value:
        if arcpy.Exists(parameterSource.valueAsText):
            # Get fields
            for field in arcpy.Describe(parameterSource.valueAsText).fields:
                parameterField.filter.list.append(field.name)
            if strDefaultFieldName:
                if strDefaultFieldName in parameterField.filter.list:
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


def testFType(parameter, ftype):
    """
    Checks if the input stream network feature class includes features where FType == 336 (i.e. canals)
    :param parameter: input stream network feature class
    :param ftype: the FType code to check
    """
    field_list = arcpy.ListFields(parameter)
    for f in field_list:
        if f.name == "FType":
            value_list = []
            with arcpy.da.SearchCursor(parameter, ["FType"]) as cursor:
                for row in cursor:
                    value = row[0]
                    value_list.append(value)
            unique_values = set(val for val in value_list)
            if ftype in unique_values:
               arcpy.AddError("Stream features where FType = 336 must be removed from the input shapefile.")
    return


# Common params
paramRiverscapesBool = arcpy.Parameter(
    displayName="Is this a Riverscapes Project?",
    name="RiverscapesBool",
    datatype="GPBoolean",
    parameterType="Optional",
    direction="Input",
    category='Riverscapes Project Management')

paramProjectXML = arcpy.Parameter(
    displayName="GNAT Project XML",
    name="projectXML",
    datatype="DEFile",
    parameterType="Optional",
    direction="Input",
    category='Riverscapes Project Management')
paramProjectXML.filter.list = ["xml"]

paramRealization = arcpy.Parameter(
    displayName="Realization Name",
    name="realization",
    datatype="GPString",
    parameterType="Optional",
    direction="Input",
    category='Riverscapes Project Management')
paramRealization.enabled = "False"

paramSegmentAnalysisName = arcpy.Parameter(
    displayName="Segmentation Name",
    name="analysisName",
    datatype="GPString",
    parameterType="Optional",
    direction="Input",
    category='Riverscapes Project Management')
paramSegmentAnalysisName.enabled = "False"

paramAttributeAnalysisName = arcpy.Parameter(
    displayName="Attribute Analysis Name",
    name="attributeAnalysisName",
    datatype="GPString",
    parameterType="Optional",
    direction="Input",
    category='Riverscapes Project Management')
paramAttributeAnalysisName.enabled = "False"

paramStreamNetwork = arcpy.Parameter(
    displayName="Input Stream Network",
    name="InputFCStreamNetwork",
    datatype="DEFeatureClass",
    parameterType="Required",
    direction="Input")
paramStreamNetwork.filter.list = ["Polyline"]

paramTempWorkspace = arcpy.Parameter(
    displayName="Temporary Workspace (uses in_memory if blank)",
    name="TempWorkspace",
    datatype="DEWorkspace",
    parameterType="Optional",
    direction="Input")
paramTempWorkspace.filter.list = ["Workspace"]