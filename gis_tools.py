# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        GIS Tools Module                                               #
# Purpose:     Support components for Riverstyles and Stream Network Toolbox  #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Version:     1.3                                                            #
# Modified:    2015-Aug-12                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import arcpy

scratchWorkspace = arcpy.env.scratchWorkspace

# # Functions # #
def resetData(inputDataset):
    if arcpy.Exists(inputDataset):
        arcpy.Delete_management(inputDataset)

    return

def newGISDataset(workspace, inputDatasetName):
    """ workspace = "LAYER", "in_memory", folder or gdb"""
    if arcpy.Exists(workspace):
        if arcpy.Describe(workspace).workspaceType == "LocalDatabase" or workspace == "in_memory":
            ext = ""
        else:
            ext = ".shp"

    if workspace == "LAYER" or workspace == "layer" or workspace == "Layer":
        inputDataset = inputDatasetName
        if arcpy.Exists(inputDataset):
            arcpy.Delete_management(inputDataset)
    else:
        inputDataset = workspace + "\\" + inputDatasetName + ext
        if arcpy.Exists(inputDataset):
            arcpy.Delete_management(inputDataset)

    return inputDataset

def getGISDataset(workspace,inputDatasetName):
    if workspace == "Layer":
        inputDataset = inputDatasetName
        if arcpy.Exists(inputDataset):
            return inputDataset
    else:
        inputDataset = workspace + "\\" + inputDatasetName
        if arcpy.Exists(inputDataset):
            return inputDataset

def resetField(inTable,FieldName,FieldType,TextLength=0):
    """clear or create new field.  FieldType = TEXT, FLOAT, DOUBLE, SHORT, LONG, etc."""
    
    if arcpy.Describe(inTable).dataType == "ShapeFile":
        FieldName = FieldName[:10]

    if len(arcpy.ListFields(inTable,FieldName))==1:
        if FieldType == "TEXT":
            arcpy.CalculateField_management(inTable,FieldName,"''","PYTHON")
        else:
            arcpy.CalculateField_management(inTable,FieldName,"0","PYTHON")
        #arcpy.DeleteField_management(inTable,FieldName) #lots of 999999 errors 
    
    else: #Create Field if it does not exist
        if FieldType == "TEXT":
            arcpy.AddField_management(inTable,FieldName,"TEXT",field_length=TextLength)
        else:
            arcpy.AddField_management(inTable,FieldName,FieldType)
    return str(FieldName) 

def addUniqueIDField(fcInputFeatureClass,fieldName):

    resetField(fcInputFeatureClass,fieldName,"LONG")
    arcpy.AddField_management(fcInputFeatureClass,fieldName,"LONG")
    codeBlock = """
counter = 0
def UniqueID():
    global counter
    counter += 1
    return counter"""

    arcpy.CalculateField_management(fcInputFeatureClass,fieldName,"UniqueID()","PYTHON",codeBlock)

    return fieldName

def unique_values(table, field):
    """returns a sorted list of unique values in a field
    
    Reference: https://arcpy.wordpress.com/2012/02/01/create-a-list-of-unique-field-values/
    """

    with arcpy.da.SearchCursor(table, [field]) as cursor:
        return sorted({row[0] for row in cursor})

### Experimental ###
class WorkspaceManager(object):
    """ object to manage files while geoprocessing """

    def __init__(self,temporaryWorkspace,outputWorkspace):
        
        self.outputWorkspace = outputWorkspace
        self.tempWorkspace = temporaryWorkspace
        self.listTempFiles = []
        self.listOutputFiles = []
        return

    def tempLayer(self,layerName):
        if arcpy.Exists(layerName):
            arcpy.Delete_management(layerName)
        return layerName 

    def outputDataset(self,filename):
        
        outputFileName = newGISDataset(self.outputWorkspace,filename)
        self.listOutputFiles.append(outputFileName)
        
        return outputFileName

    def tempDataset(self,filename):        
        
        tempFileName = newGISDataset(self.tempWorkspace,filename)
        self.listTempFiles.append(tempFileName)

        return tempFileName
    
    def clearTempWorkspace(self):

        for file in self.listTempFiles:
            if arcpy.Exists(file):
                arcpy.Delete_management(file)
            self.listTempFiles = self.listTempFiles.remove(file)
        
        return 

if __name__ == "__main__":
    print("gis_tools.py is not an executable python script.")

