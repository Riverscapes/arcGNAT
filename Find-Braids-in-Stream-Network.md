The **Find Braids in Stream Network** tool is used to determine if segments/branches are part of a braided section of the stream network. This is useful for data validation and repair of the stream network polyline feature class. 

---
##Usage##
###Input Parameters

**Input Stream Network**

Stream network to check for braids.

* This tool modifies input dataset:
	* Adds (or overwrites) `IsBraidedReach` Field:
		* Value = 1: Segment is part of a braided section of the network
		* value = 0: Segment is not part of a braided section of the network.

### Geoprocessing Environments
* It is recommended to run this tool in 64-bit python geoprocessing.
* Disable Z and M if you encounter a topology error.

---
## Technical Background
###Calculation Method

1. Convert stream network to polygons. Features will form at all closed parts of the network.
2. Select segments that share a line with the polygons
3. Calculate Field (“IsBraidedReach” = 1) on the selection.