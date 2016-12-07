The **Stream Sinuosity and Planform** tool calculates sinuosity (per segment) for valley centerline and flowline network. Also transfers the valley sinuosity to the stream network and calculates river planform attribute.

### Geoprocessing Environments###
* All inputs must be in th same projected coordinate system.
* It is recommended to run this tool with 64-bit python geoprocessing.
* Disable Z and M if you encounter a topology error.

## Input Parameters

### Input Stream Network

Segmented Stream Network (i.e. flowline, centerline, etc). Stream Sinuosity will be calculated for each segment.

### Valley Centerline

Segmented Valley Bottom Centerline. Valley Sinuosity will be calculated for each segment.

###Valley Bottom Polygon

The valley bottom polygon of the stream network. This is used in the Transfer Line Attribute tool.

> This required input will be depreciated in a future version of this tool.

### Output Stream Network with Sinuosity Attribute

Output Polyline Feature Class (in a FGDB) for saving the segmented stream Network with calculated sinuosity.

### Output Valley Centerline with Sinuosity Attribute

Output Polyline Feature Class (in a FGDB) for storing the Valley Bottom Centerline with 
calculated sinuosity.

### Output Stream Network with Planform Attribute

Output Polyline Feature Class (in a FGDB) for storing the stream Centerline with calculated Planform attribute.

##Calculation Method##
The Stream Sinuosity and Planform Tool uses the following calculation method:

1. Use Sinuosity By Segment Tool for stream and valley centerlines
	1. Convert segment ends to points
	2. Use Points to Line to find straight line distance
	3. calculate sinuosity (Straight distance/segment distance)
2. Transfer Valley Bottom Sinuosity to Stream Centerline using Transfer Line Attribute Tool
3. Calculate Planform metric for each divided segment

##Outputs##

***Output Stream Centerline With Sinuosity***


***Output Valley Centerline with Sinuosity***


***Output Planform Network***


##Troubleshooting and Potential Issues##
Planform attribute relies on the accuracy and performance of the Transfer Attribute Tool (Testing in progress).
Need better understanding of desired segmentation lengths.

##References and Resources##