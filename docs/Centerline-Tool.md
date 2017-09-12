---
title: Centerline Tool
---


The **Centerline** tool from the FluvialCorridor Toolbox has been modified and imported inside the Stream Network and RiverStyles toolbox. The modifications fix 1) missing centerlines in sections of the valley bottom polygon and 2) extra centerline segments.

Please reference the [FluvialCorridor Toolbox](http://www.sciencedirect.com/science/article/pii/S0169555X14002219) for additional information on the **Centerline** tool.

_______________________________________________________________
## Usage

### Geoprocessing Environments

* It is recommended to run this tool using 64-bit python geoprocessing.
* Disable Z and M geometry in the Shape field if topology errors are encountered.
* Specify a scratch workspace to save/review intermediate temporary files.

### Input Parameters

![centerline_form]({{site.baseurl}}/images/centerline_form.PNG)

**Valley bottom polygon feature class**

Should be a `valley bottom polygon`, which is an data output of the [Valley Bottom Extraction Tool (VBET)](https://bitbucket.org/jtgilbert/riparian-condition-assessment-tools/wiki/Tool_Documentation/VBET).

Requirements:

* Single part
* Only one feature within the polygon feature class

**Stream network polyline feature class**

A stream network polyline feature class. The **Centerline** tool will create a centerline in sections of the valley bottom polygon where the stream network exists.

Requirements:

* Line network should be contained inside the valley bottom polygon feature class input.
* Remove any "dangles' or other artificially short line segments attached to the network. Dangles will cause extraneous centerlines to be created. 

**Disaggregation step**

Length used to split the valley bottom polygon margins when creating Thiessen polygons

> TIP: Use smaller values (i.e 10m-25m) to maintain detail in narrow reaches.

**Smoothing tolerance**

Smoothing tolerance for the final centerline. 

> TIP: 20m recommended.

**Output centerline**

Output name and location of a polyline feature class containing the new centerline.

**Delete temporary files**

If checked, deletes temporary processing files after the tool completes.

### Outputs

**Output Centerline Feature Class**

Polyline feature class representing the valley bottom centerline. 

_______________________________________________________________
## Technical Background

### Troubleshooting and Potential Issues###
1. Extraneous centerlines, usually short spurs.
2. Centerline that does not follow the entire valley length.
3. Centerline may include bends at the end of some valleys.

### References and Resources

* [FluvialCorridor Toolbox](http://umrevs-isig.fr/spip.php?rubrique164)
* Other methods for centerline generation
	* http://www1.pub.informatik.uni-wuerzburg.de/pub/haunert/pdf/HaunertSester2008.pdf
	* http://gis.stackexchange.com/questions/2775/find-tunnel-center-line
	* http://gis.stackexchange.com/questions/29863/creating-centrelines-from-road-polygons-casings
	* https://geonet.esri.com/thread/11548