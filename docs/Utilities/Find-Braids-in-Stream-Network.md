---
title: Find Braids in Stream Network
---


The **Find Braids in Stream Network** tool determines if stream reaches are part of a braided section of a stream network polyline feature class. Stream reach features that are braids can then be identified by selecting all records where "IsBraidedReach" == 1. This is useful for data validation and repair of the polyline feature class, and is incorporated into the processing workflow of the [Find Network Errors](http://gnat.riverscapes.net/Find-Network-Features) tool. 

![braids_example]({{site.baseurl}}assets/images/braids_example.png)

_______________________________________________________________
## Usage

### Geoprocessing Environments
* We recommend running this tool with 64-bit python geoprocessing.
* Disable Z and M geometry in the Shape field if topology errors are encountered.

### Input Parameters

![braids_form]({{site.baseurl}}assets/images/braids_form.PNG)


**Input Stream Network**

Stream network polyline feature class that will be checked for braided features.
The input polyline feature class will be modified.
* Adds (or overwrites) `IsBraidedReach` attribute field:
	* Value = 1: Segment is part of a braided section of the stream network
	* Value = 0: Segment is not part of a braided section of the stream network

_______________________________________________________________
## Technical Background

###Calculation Method

1. Convert the stream network polyline features to polygons. Polygon features will be generated at all closed parts of the network.
2. Select network segments that share a line with the polygon features.
3. Calculate field (“IsBraidedReach” = 1) for selected features.