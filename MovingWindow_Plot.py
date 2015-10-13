# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Plot Moving Window Analysis Results                            #
# Purpose:     Plot results from  a generic moving window analysis for a      #
#              variable along a line network.                                 #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Oct-06                                                    # 
# Version:     1.3                                                            #
# Modified:    2015-Oct-06                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import os
import sys
import arcpy
import matplotlib.pyplot as plt
import numpy


# # Main Function # # 
def main(
    fcSeedPoints,
    StrFieldsWindowAnalysis,
    strlistBinClasses,
    strlistBinClassNames):
    """Analyze MWA Results."""

    listFieldsWindowAnalysis = StrFieldsWindowAnalysis.split(";")
    listBinClasses = [float(i) for i in strlistBinClasses.split(";")] # Convert string to list of float
    listBinClassNames = strlistBinClassNames.split(";")
    # Prepare Dataplot

    with arcpy.da.SearchCursor(fcSeedPoints,listFieldsWindowAnalysis) as scSeedPoints:
        arrayListWindowData = [[] for _ in xrange(int(len(listFieldsWindowAnalysis)))]
        for row in scSeedPoints:
            i = 0
            for item in row:
                arrayListWindowData[i].append(item)
                i = i + 1

    vals = []
    
    for listWindowData in arrayListWindowData:
        hist,edges = numpy.histogram(listWindowData,listBinClasses,range=(0,1))
        normalizedVals=[]
        dblSum = numpy.sum(hist)
        for value in hist:
            NormalizedValue = float(value)/dblSum
            normalizedVals.append(NormalizedValue)
        vals.append(normalizedVals)

    newvals = [list(i) for i in zip(*vals)]
    pos = numpy.arange(int(len(listFieldsWindowAnalysis)))+.5    # the bar centers on the y axis

    
    # Plot
    fig = plt.figure()
    colorRamp = ['green','yellow','orange','red']
    ax = fig.add_subplot(111)
    lefts = 0
    i = 0
    for val in newvals:
        ax.barh(pos,
                val, 
                align='left',
                left=lefts,
                color=colorRamp[i],#numpy.random.rand(3,1),
                label=listBinClassNames[i])
        #set_xlabels(listBinClassNames)
        #for p in pos:
            #ax.text(p,i,listBinClassNames[i],ha='center',va='center')
        lefts = val
        i=i+1

    plt.yticks(pos, listFieldsWindowAnalysis)
    plt.xlabel('Percent')
    plt.title('Moving Window Analysis Comparison')
    plt.legend()
    plt.grid(True)
    plt.show()
    
    # some labels for each row
    people = listFieldsWindowAnalysis #('A','B','C','D','E','F','G','H')
    r = len(people)

    # how many data points overall (average of 3 per person)
    n = r * 3

    # which person does each segment belong to?
    rows = pos #numpy.random.randint(0, r, (n,))
    # how wide is the segment?
    widths = numpy.random.randint(3,12, n,)
    # what label to put on the segment
    labels = xrange(n)
    colors ='rgbwmc'

    patch_handles = []

    fig = plt.figure(figsize=(10,8))
    ax = fig.add_subplot(111)

    #####

    left = numpy.zeros(r,)
    row_counts = numpy.zeros(r,)

    for (r, w, l) in zip(rows, widths, labels):
        print r, w, l
        patch_handles.append(ax.barh(r, w, align='center', left=left[r],
            color=colors[int(row_counts[r]) % len(colors)]))
        left[r] += w
        row_counts[r] += 1
        # we know there is only one patch but could enumerate if expanded
        patch = patch_handles[-1][0] 
        bl = patch.get_xy()
        x = 0.5*patch.get_width() + bl[0]
        y = 0.5*patch.get_height() + bl[1]
        ax.text(x, y, "%d%%" % (l), ha='center',va='center')

    y_pos = numpy.arange(8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(people)
    ax.set_xlabel('Distance')

    plt.show()


    


    # Save Plot





if __name__ == "__main__":

    main(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4])