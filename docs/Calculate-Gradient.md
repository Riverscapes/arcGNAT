---
title: Calculate Gradient
---


Stream gradient is the grade in elevation measured by the ratio of drop in elevation of a stream, per unit of 
horizontal distance. The **Calculate Gradient** tool calculates stream gradient per feature in a stream network. 
Specifically, the tool calculates gradient by measuring the difference in elevation between the start and end nodes
of each stream feature (i.e. reach or segment) within the network, then dividing by the reach length value.

![gradient_example]({{site.baseurl}}/images/gradient_example.png)

_______________________________________________________________

## Usage


### Geoprocessing Environment

* We recommend running the tool using 64-bit python geoprocessing.
* Disable Z and M values in the input stream network feature class Shape field.

### Input Parameters

**Input Stream Network**

* Stream network polyline feature class which will used in gradient calculations. 

**Elevation (DEM) Raster Dataset**

* Raster dataset with values representing bare earth elevation (i.e. a digital elevation model).

### Output

* The **Calculate Gradient** tool currently appends new gradient attribute fields to the `Input Stream Network`. 
  Values are calculated per stream feature. New attribute fields will appended to this dataset on completion of the 
  processing, including:

  * ELEV_START - elevation (in native units of input raster dataset) of 'From' node
  * ELEV_END - elevation of 'To' node
  * GRADIENT - calculated per stream feature as **ELEVATION DIFFERENCE / LENGTH_M**
  * LENGTH_M - length in meters per stream feature
  
  *Please note*: If this analysis is part of Riverscapes project, the `Input Stream Network` will automatically
  be switched to the stream network feature class associated with the Realization Analysis found in the project.rs.xml
  file, which the user selects in the `Riverscape Project Management` parameters of this tool.
  
### Riverscapes Project Management

**Is this a Riverscapes Project?** (optional)

* Check box indicating whether this analysis is part of an existing Riverscapes project.

**GNAT Project XML** (optional)

* XML file (should be named `project.rs.xml`) which stores information on the associated Riverscapes project.

**Realization Name** (optional)

* Name of the project Realization selected from a list of existing Realizations. Only one Realization can be selected.

**Segmentation Name** (optional)

* Name of the Segmentation Analysis selected from a list of existing Analyses, to which the Calculate Gradient 
analysis will be assigned.

**Attribute Analysis Name** (optional)

* Name of the new Calculate Gradient analysis.
_______________________________________________________________

## Technical Background

### Calculation Method

1. Plot the start (i.e. 'From') and end (i.e. 'To') points of each stream feature.
2. Add new attribute fields to the node feature class, to store X and Y coordinates, as well as elevation values.
3. Calculate X and Y coordinates (in the native coordinate system of the input stream network)
4. Extract elevation values from raster dataset for each node point.
5. Add start and end elevation values as attributes to corresponding linear stream features.
6. Calculate length in meters, per stream feature.
7. Calculate difference in elevation between start and end nodes.
8. Calculate gradient

### Troubleshooting and Potential Issues

Because the gradient calculation is dependent on accurate elevation values at the start and end nodes of 
each stream feature, care should be taken to ensure that the spatial (i.e. grid cell) resolution of the 
elevation raster dataset is appropriate to the scale and stream feature length of the input stream network 
feature class.


