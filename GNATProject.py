"""Confinement Project"""

from os import path
import xml.etree.ElementTree as ET


class RiverscapesProject(object):
    """Riverscapes Project Class
    Represent the inputs, realizations and outputs for a confinement project and read,
    write and update xml project file."""

    def __init__(self):

        self.name = ''
        self.projectType = ""
        self.projectPath = ''

        self.ProjectMetadata = {}
        self.Realizations = {}
        self.InputDatasets = {}

    def create(self,projectName,projectType):

        self.name = projectName
        self.projectType = projectType

    def addProjectMetadata(self,Name,Value):
        self.ProjectMetadata[Name] = Value

    def addInputDataset(self, name, id, relativePath, sourcePath):

        newInputDataset = dataset()
        newInputDataset.create(name,relativePath,origPath=sourcePath)

        int = len(self.InputDatasets)
        newInputDataset.id = id
        self.InputDatasets[newInputDataset.name] = newInputDataset

    def get_dataset_id(self,absfilename):

        relpath = path.relpath(absfilename,self.projectPath)
        id = ""

        for name,dataset in self.InputDatasets.iteritems():
            if relpath == dataset.relpath:
                id = dataset.id

        return id

    def loadProjectXML(self,XMLpath):

        # Open and Verify XML.
        tree = ET.parse(XMLpath)
        root = tree.getroot()
        # TODO Validate XML, If fail, throw validation error
        # TODO Project Type self.projectType == "Confinement"

        # Load Project Level Info
        self.name = root.find("Name").text
        for meta in root.findall("./MetaData/Meta"):
            self.ProjectMetadata[meta.get("name")] = meta.text

        # Load Input Datasets
        for inputDatasetXML in root.findall("./Inputs/Vector"):
            inputDataset = dataset()
            inputDataset.createFromXMLElement(inputDatasetXML)
            self.InputDatasets[inputDataset.id] = inputDataset

        # Load Realizations
        for realizationXML in root.findall("./Realizations/Confinement"): #TODO: genericize CONFINEMENT
            realization = ConfinementRealization()
            realization.createFromXMLElement(realizationXML, self.InputDatasets)
            self.Realizations[realization.name] = realization

        # TODO Link Realizations with inputs?

        self.projectPath = path.dirname(XMLpath)

        return

    def addRealization(self, realization):

        intRealizations = len(self.Realizations)
        realization.id = "Confinement_" + str(intRealizations + 1) #TODO: Remove Confinement

        self.Realizations[realization.name] = realization
        return

    def writeProjectXML(self,XMLpath):

        rootProject = ET.Element("Project")
        rootProject.set("xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance")
        rootProject.set("xsi:noNamespaceSchemaLocation","https://raw.githubusercontent.com/Riverscapes/Program/master/Project/XSD/V1/Project.xsd")

        nodeName = ET.SubElement(rootProject,"Name")
        nodeName.text = self.name

        nodeType = ET.SubElement(rootProject,"ProjectType")
        nodeType.text = self.projectType

        nodeMetadata = ET.SubElement(rootProject,"MetaData")
        for metaName,metaValue in self.ProjectMetadata.iteritems():
            nodeMeta = ET.SubElement(nodeMetadata,"Meta",{"name":metaName})
            nodeMeta.text = metaValue

        if len(self.InputDatasets) > 0:
            nodeInputDatasets = ET.SubElement(rootProject,"Inputs")
            for inputDatasetName,inputDataset in self.InputDatasets.iteritems():
                nodeInputDataset = inputDataset.getXMLNode(nodeInputDatasets)

        if len(self.Realizations) > 0:
            nodeRealizations = ET.SubElement(rootProject,"Realizations")
            for realizationName, realizationInstance in self.Realizations.iteritems():
                nodeRealization = realizationInstance.getXMLNode(nodeRealizations)

        indent(rootProject)
        tree = ET.ElementTree(rootProject)
        tree.write(XMLpath,'utf-8',True)

        # TODO Add warning if xml does not validate??

        return


class GNATRealization(object):
    # TODO make gnat realization
    def __init__(self):

        self.promoted = ''
        self.dateCreated = ''
        self.productVersion = ''
        self.guid = ''
        self.name = ''
        self.id = 'Not_Assigned'


    def create(self):

        return



class ConfinementRealization(object):

    def __init__(self):

        self.promoted = ''
        self.dateCreated = ''
        self.productVersion = ''
        self.guid = ''
        self.name = ''
        self.id = 'Not_Assigned'

        self.StreamNetwork = ''
        self.ValleyBottom = ''
        self.ChannelPolygon = ''

        self.OutputConfiningMargins = dataset()
        self.OutputRawConfiningState = dataset()

        self.analyses = {}

    def create(self, name, refStreamNetwork, refValleyBottom, refChannelPolygon, OutputConfiningMargins, OutputRawConfiningState):
        """
        :param str name:
        :param str refStreamNetwork:
        :param str refValleyBottom:
        :param str refChannelPolygon:
        :param dataset OutputConfiningMargins:
        :param dataset OutputRawConfiningState:
        :return: none
        """

        self.promoted = ''
        self.dateCreated = ''
        self.productVersion = ''
        self.guid = ''
        self.name = name

        # StreamNetwork.type = "StreamNetwork"
        # ValleyBottom.type = "ValleyBottom"
        # ChannelPolygon.type = "ChannelPolygon"

        OutputConfiningMargins.type = "ConfiningMargins"
        OutputConfiningMargins.xmlSourceType = "ConfiningMargins"
        OutputRawConfiningState.type = "RawConfiningState"
        OutputRawConfiningState.xmlSourceType = "RawConfiningState"

        self.StreamNetwork = refStreamNetwork
        self.ValleyBottom = refValleyBottom
        self.ChannelPolygon = refChannelPolygon

        self.OutputConfiningMargins = OutputConfiningMargins
        self.OutputRawConfiningState = OutputRawConfiningState

    def createFromXMLElement(self, xmlElement,dictInputDatasets):

        # Pull Realization Data
        self.promoted =  xmlElement.get("promoted")
        self.dateCreated = xmlElement.get("dateCreated")
        self.productVersion = xmlElement.get('productVersion')
        self.id = xmlElement.get('id')
        self.guid = xmlElement.get('guid')

        self.name = xmlElement.find('Name').text

        # Pull Inputs
        self.ValleyBottom = xmlElement.find('./Inputs/ValleyBottom').get('ref')
        self.ChannelPolygon = xmlElement.find('./Inputs/ChannelPolygon').get('ref')
        self.StreamNetwork = xmlElement.find('./Inputs/StreamNetwork').get('ref')

        # Pull Outputs
        self.OutputConfiningMargins.createFromXMLElement(xmlElement.find("./Outputs/ConfiningMargins"))
        self.OutputRawConfiningState.createFromXMLElement(xmlElement.find("./Outputs/RawConfiningState"))

        # Pull Analyses
        for analysisXML in xmlElement.findall("./Analyses/*"):
            analysis = Analysis()
            analysis.createFromXMLElement(analysisXML)
            self.analyses[analysis.name] = analysis
        return

    def getXMLNode(self,xmlNode):

        # Prepare Attributes
        attributes = {}
        attributes['promoted'] = self.promoted
        attributes['dateCreated'] = self.dateCreated
        attributes['id'] = self.id
        if self.productVersion:
            attributes['productVersion'] = self.productVersion
        if self.guid:
            attributes['Guid'] = self.guid

        # Create Node
        nodeRealization = ET.SubElement(xmlNode,"Confinement",attributes)
        nodeConfiementName = ET.SubElement(nodeRealization,"Name")
        nodeConfiementName.text = self.name

        # Realization Inputs
        nodeRealizationInputs = ET.SubElement(nodeRealization,"Inputs")
        nodeValleyBottom = ET.SubElement(nodeRealizationInputs,"ValleyBottom")
        nodeValleyBottom.set("ref",self.ValleyBottom)
        nodeChannelPolygon = ET.SubElement(nodeRealizationInputs,"ChannelPolygon")
        nodeChannelPolygon.set("ref",self.ChannelPolygon)
        nodeStreamNetwork = ET.SubElement(nodeRealizationInputs,"StreamNetwork")
        nodeStreamNetwork.set('ref',self.StreamNetwork)

        nodeOutputs = ET.SubElement(nodeRealization,"Outputs")
        self.OutputRawConfiningState.getXMLNode(nodeOutputs)
        self.OutputConfiningMargins.getXMLNode(nodeOutputs)

        #Realization Analyses
        nodeAnalyses = ET.SubElement(nodeRealization,"Analyses")
        for analysisName,analysis in self.analyses.iteritems():
            analysis.getXMLNode(nodeAnalyses)

        return nodeRealization

    def newAnalysisMovingWindow(self,analysisName,paramSeedPointDist,paramWindowSizes,outputSeedPoints,outputWindows):

        analysis = Analysis()
        analysis.create(analysisName,"MovingWindow")

        analysis.parameters["SeedPointDistance"] = paramSeedPointDist
        analysis.parameters["WindowSizes"] = paramWindowSizes
        analysis.outputDatasets["SeedPointFile"] = outputSeedPoints
        analysis.outputDatasets["MovingWindowFile"] = outputWindows

        self.analyses[analysisName] = analysis


    def newAnalysisSegmentedNetwork(self, analysisName,paramFieldSegments,paramFieldConfinement,paramFieldConstriction,outputSegmentedConfinement):

        analysis = Analysis()
        analysis.create(analysisName, "SegmentedNetwork")

        analysis.parameters["SegmentField"] = paramFieldSegments
        analysis.parameters["ConfinementField"] = paramFieldConfinement
        analysis.parameters["ConstrictionField"] = paramFieldConstriction
        analysis.outputDatasets["SegmentedConfinement"] = outputSegmentedConfinement

        self.analyses[analysisName] = analysis

        return




class Analysis(object):

    def __init__(self):
        self.name = ''
        self.type = ''
        self.parameters = {}
        self.outputDatasets = {}

    def create(self,analysisName,analysisType):
        self.name = analysisName
        self.type = analysisType
        return

    def createFromXMLElement(self,xmlElement):

        self.type = xmlElement.tag
        self.name = xmlElement.find("Name").text

        for param in xmlElement.findall("./Parameters/Param"):
            self.parameters[param.get('name')] = param.text

        for output in xmlElement.findall("./Outputs/*"):
            outputDS = dataset()
            outputDS.createFromXMLElement(output)
            self.outputDatasets[outputDS.name] = outputDS

        return

    def addParameter(self,parameterName,parameterValue):
        self.parameters[parameterName] = parameterValue
        return

    def getXMLNode(self,xmlNode):

        nodeAnalysis = ET.SubElement(xmlNode,self.type)

        nodeAnalysisName = ET.SubElement(nodeAnalysis,'Name')
        nodeAnalysisName.text = self.name

        nodeParameters = ET.SubElement(nodeAnalysis,"Parameters")
        for paramName,paramValue in self.parameters.iteritems():
            nodeParam = ET.SubElement(nodeParameters,"Param",{"name":paramName})
            nodeParam.text = paramValue

        nodeOutputs = ET.SubElement(nodeAnalysis,"Outputs")
        for outputName,outputDataset in self.outputDatasets.iteritems():
            outputDataset.getXMLNode(nodeOutputs)

        #TODO Writing Analysis Node

        return xmlNode


class dataset(object):

    def __init__(self):
        self.id = 'NotAssinged' # also ref
        self.name = ''
        self.guid = ''
        self.type = ''
        self.relpath = ''
        self.metadata = {}

    def create(self, name, relpath, type="Vector",guid='',origPath=""):

        self.name = name # also ref
        self.guid = guid
        self.type = type
        self.relpath = relpath

        self.id = "NotAssigned" # TODO make this unique!!!!

        if origPath:
            self.metadata["origPath"] = origPath

    def createFromXMLElement(self, xmlElement):

        self.id = xmlElement.get("id")
        self.guid = xmlElement.get('Guid')
        self.name = xmlElement.find('Name').text
        self.relpath = xmlElement.find("Path").text

        self.type = xmlElement.tag

        for nodeMeta in xmlElement.findall("./MetaData/Meta"):
            self.metadata[nodeMeta.get('name')] = nodeMeta.text

    def getXMLNode(self,xmlNode):

        #Prepare Attributes
        attributes = {}
        attributes["id"] = self.id
        if self.guid:
            attributes['Guid'] = self.guid

        # Generate Node
        nodeInputDataset = ET.SubElement(xmlNode,self.type,attributes)

        nodeInputDatasetName = ET.SubElement(nodeInputDataset, "Name")
        nodeInputDatasetName.text = self.name
        nodeInputDatasetPath = ET.SubElement(nodeInputDataset,"Path")
        nodeInputDatasetPath.text = self.relpath

        if self.metadata:
            nodeInputDatasetMetaData = ET.SubElement(nodeInputDataset,"MetaData")
            for metaName, metaValue in self.metadata.iteritems():
                nodeInputDatasetMeta = ET.SubElement(nodeInputDatasetMetaData,"Meta",{"name":metaName})
                nodeInputDatasetMeta.text = metaValue

        return xmlNode

    def absolutePath(self,projectPath):

        return path.join(projectPath,self.relpath)


def get_input_id(inpath,strInputName):

    import glob

    int_id = len(glob.glob(path.join(inpath, strInputName + "*"))) + 1

    return strInputName + str(int_id).zfill(3)


def indent(elem, level=0, more_sibs=False):
    """ Pretty Print XML Element
    Source: http://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
    """

    i = "\n"
    if level:
        i += (level-1) * '  '
    num_kids = len(elem)
    if num_kids:
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
            if level:
                elem.text += '  '
        count = 0
        for kid in elem:
            indent(kid, level+1, count < num_kids - 1)
            count += 1
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
            if more_sibs:
                elem.tail += '  '
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
            if more_sibs:
                elem.tail += '  '


def get_program_watersheds():

    listWatersheds = []

    return listWatersheds