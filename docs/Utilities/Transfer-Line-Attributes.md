---
title: Transfer Line Attributes
---

The **Transfer Line Attributes** tool transfers attributes between stream network polyline feature classes, using a segmented polygon approach. The segmented polygons are generated using Thiessen polygons in the [Divide Polygons by Segments](http://gnat.riverscapes.xyz/Divide-Polygon-by-Segments) tool. Alternatively, this tool can use Branch IDs from both networks datasets to better manage tributary junctions. 

_______________________________________________________________
## Usage

### Geoprocessing Environments

* We recommended running this tool using 64-bit python geoprocessing.
* Disable Z and M if you encounter a topology error.
* Both input datasets must use the same projected coordinate system.
* The "From" network is segmented (the "To" network may also be segmented) and attributed as desired.

### Input Parameters

![transfer_form]({{site.baseurl}}assets/images/transfer_form.PNG)

**Input “From” polyline feature class**

The polyline feature class from which attributes will be transferred. This feature class is used to "resegment" the “To” line network.

**Input “To” polyline feature class**

The polyline feature class that will receive the attributes from the “From” network. This feature class will retain its segmentation and attributes, but will also be resegmented based on the transfer of the “From” polyline feature class. This allows both the new and original attributes to exist in the resulting network.

**Output polyline feature class**

Polyline feature class that will contain the resulting line network with transferred ("From") and original("To") attributes.

**Search distance** (optional)

Distance (in meters) that the tool will use to search for nearby junction points between the "From"
and "To" networks.

**Scratch workspace** (optional)

Local folder for storing temporary data during processing.

_______________________________________________________________
## Technical Background

### Calculation Method

1. Divide polygon into segments based on segmentation/junctions in the “From” line network, using the [Divide Polygons by Segments](http://gnat.riverscapes.xyz/Divide-Polygon-by-Segments) tool.
2. Split “To” line network based on the intersection of the divided polygons.
3. Transfer “From” network OID’s to polygon segments.
4. Spatially join the segmented polygons the “To” line network feature centroids.
5. Copy attributes from segmented polygons to the line features.

### Troubleshooting and Potential Issues
* Line features in the 'To' network with no associated features in the 'To' network are assigned the value '-99999'
* Tributary junctions may cause suboptimal results