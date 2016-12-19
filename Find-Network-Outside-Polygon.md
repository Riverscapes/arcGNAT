The **Find Streams Outside Valley Bottom** tool finds stream network segments that fall outside of the valley bottom polygon boundary.  The valley bottom polygon can then be manually edited to encompass these segments.

_______________________________________________________________
## Usage

### Input Parameters

[[images/find_network_form.PNG]]

**Input Stream Network** 

The feature class you are cleaning.  This should be a projected stream network.

**Input Valley Bottom**

The valley bottom polygon you have created and are editing.

**Scratch Workspace**

File geodatabase or folder, where temporary data will be stored during processing. 

**Output Workspace**

*** Stream network polyline feature class
File geodatabase or folder where output the polyline feature class will be stored.

The output feature class will contain an attribute field called `InVB` which contains either a `Yes` or a blank.  Segments with blanks fall outside of the valley bottom polygon and are selected in a final output file.  Use these features to find areas which need to be edited in the valley bottom polygon.

_______________________________________________________________
## Technical Background

### Calculate Method
1. Intersect input polyline feature class with input valley bottom polygon.
2. Dissolve intersected feature class and valley bottom by GNIS_ID and GNIS_Name.
3. Add attribute field `InVB` to dissolved feature class.
4. Calculate all records in 'InVB' field with "Yes" value.
5. Create feature class of endpoints from stream network.
6. Split the original stream network by the points of the network inside the valley bottom.
7. Create feature class of stream segment midpoints.
8. Join midpoint feature class to dissolved stream network polyline feature class.
9. Join split polyline feature class with joined feature class.
10. Select polyline features that fall outside of the valley bottom polygon boundary and create output feature class.
