# -*- coding: utf-8 -*-

'''
Created on 21 fev. 2013
Last update on 07 fev. 2014

@author: Clement Roux

@contact: clement.roux@ens-lyon.fr
          CNRS - UMR5600 Environnement Ville Societe
          15 Parvis Ren?escartes, BP 7000, 69342 Lyon Cedex 07, France
         
@note: For each use of the FluvialCorridor toolbox leading to a publication, report, presentation or any other
       document, please refer the following article :
       Roux, C., Alber, A., Bertrand, M., Vaudor, L., Piegay, H., submitted. "FluvialCorridor": A new ArcGIS 
       package for multiscale riverscape exploration. Geomorphology
       
@summary: def__ExtremePoints is an open-source python and arcPy code.
          This script is used within the "Centerline" module of the FluvialCorridor package. It enables to
          extract only the extreme points of a network (sources and outlet).
          
'''


# Import of required librairies
import arcpy
import collections
import def__ScratchWPathName as SWPN
from tools.FCT import def__Export as Exp

# Allow the temporary outputs overwrite
arcpy.env.overwriteOutput = True

#===============================================================================
# CODING
#===============================================================================
def ExtremePoints (inFC):
    ScratchW = SWPN.ScratchWPathName ()
    Exp.Export(inFC, ScratchW, "ExportTable")    
    fichier = open(ScratchW + "\\ExportTable.txt", 'r')
    
    X = []
    Y = []
    XY = []
    
    head = fichier.readline().split('\n')[0].split(';')
    iX = head.index("POINT_X")
    iY = head.index("POINT_Y")
    
    for l in fichier:
        X.append(float(l.split('\n')[0].split(';')[iX]))
        Y.append(float(l.split('\n')[0].split(';')[iY]))
  
    for i in range (0, len(X)) :
        XY.append((X[i],Y[i]))
        
        
    x = list(collections.Counter(XY).most_common())
    n = 0

    for i in range(0, len(x)) :
        if x[i][1] > 1 :
            n+=1
        
    rows = arcpy.UpdateCursor(inFC)
    for line in rows :
        for cple in x[0:n] :
            if (round(line.POINT_X,1), round(line.POINT_Y,1)) == (round(cple[0][0],1), round(cple[0][1],1)) :
                line.Del = 1
                rows.updateRow(line)
                