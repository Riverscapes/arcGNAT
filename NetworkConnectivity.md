Check Network Connectivity Tool
===============================
 ##Introduction##
Tool used to determine if segments/branches are connected to the rest of the network. This is useful for data validation and repair of the Stream Network. 
Instructions

##Geoprocessing Environment##
It is recommended to run this tool in 64-bit python geoprocessing.
Disable Z and M if you encounter a topology error.

##Inputs##
Input Stream Network
Stream Network feature class to determine connected segments.

Adds (or overwrites) “IsCon” Field.
Value = 1: Segment is connected to network
value = 0: Segment is not connected to the network.

Downstream Reach ID
Specify the downstream reach of the network. Use the “active” ObjectID/FID of the feature class.

##Calculation##
Select segment ID=Input Downstream ID.
Select by location segments that intersect selection.
Repeat until the number of selected features does not change.
Calculate field of selected features (IsCon = 1)

##Output##
Tool modifies input dataset.



##Troubleshooting and Potential Issues##
Unknown how Multipart features affects the tool.
References and Resources

Revision History

###Version 1.1###