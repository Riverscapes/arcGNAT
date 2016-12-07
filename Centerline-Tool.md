*Modified from the Centerline Tool in the Fluvial Corridor Toolbox*

The Centerline Tool from the Fluvial Corridor toolbox has been modified and imported inside the Stream Network and RiverStyles toolbox. The modifications fix 1) missing centerlines in sections of the valley bottom polygon and 2) extra centerline segments.

Please reference the Fluvial corridor Toolbox for additional Information on this Tool.

## Usage

### Parameters
**Polygon**

Use the `Valley Bottom Polygon`

Requirements:

* Single Part
* Only one feature within featureclass

**Polyline**

Use the Stream Line Network. This tool will create a centerline in sections of the valley bottom polygon where the line network exists.

Requirements:

* Line network should be contained inside the Valley Bottom Polygon
* Remove any "dangles' or other artficially short line segments attached to the network. These will cause extra centerlines to be created. 

**Disaggregation Step**

length used to split up the valley bottom polygon margins for creating thiessen polygons

> TIP: Use smaller values (i.e 10m-25m) to keep detail in narrow reaches.

**Smoothing**

Smoothing tolerance for final centerline. 

> TIP: 20m is typically used.

**Output**

Output name and location of a Polyline feature class that contains the new centerline.

**Delete Temp Files**

Check to delete temporary processing files after the tool completes.

### Geoprocessing Environments

* It is recommended to run this tool in 64-bit python geoprocessing.
* Disable Z and M if you encounter a topology error.
* Make sure to specify a Scratch Workspace if you want to save/review the temp files.

### Checking the output

Erroneous features to check for

1. Extra centerlines, usually short spurs.
2. Centerlines do not follow the entire valley

## Technical Background
### Troubleshooting and Potential Issues##
Centerline bends at the end of some valleys.

### References and Resources

* [Fluvial corridor toolbox Home](http://umrevs-isig.fr/spip.php?rubrique164)
* Other Methods for centerline generation
	* http://www1.pub.informatik.uni-wuerzburg.de/pub/haunert/pdf/HaunertSester2008.pdf
	* http://gis.stackexchange.com/questions/2775/find-tunnel-center-line
	* http://gis.stackexchange.com/questions/29863/creating-centrelines-from-road-polygons-casings
	* https://geonet.esri.com/thread/11548