Stream gradient is the grade in elevation measured by the ratio of drop in elevation of a stream, per unit of horizontal distance. 
The **Calculate Gradient** tool calculates stream gradient per feature in a stream network. Specifically, the tool calculates gradient
by measuring the difference in elevation between the start and end nodes of each stream feature (i.e. reach or segment) 
within the network.

![gradient_example]({{site.baseurl}}/images/gradient_example.png)

_______________________________________________________________
##Usage

### Geoprocessing Environment

* We recommend running the tool using 64-bit python geoprocessing.
* Disable Z and M values in the input stream network feature class Shape field.

### Input Parameters

**Input Stream Network**

* Stream network polyline feature class which will used in gradient calculations. 

**Elevation (DEM) Raster Dataset**

* Raster dataset with values representing bare earth elevation (i.e. a digital elevation model).

### Output

**Output Shapefile**

* Polyline shapefile with new attributes. Values are calculated per stream feature found in
the input stream network polyline feature class.

  * ELEV_START - elevation (in native units of input raster dataset) of 'From' node
  * ELEV_END - elevation of 'To' node
  * GRADIENT - calculated per stream feature as **ELEVATION DIFFERENCE / LENGTH_M**
  * LENGTH_M - length in meters per stream feature

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
elevation raster dataset should be appropriate to the scale and stream feature length of the input stream
network feature class.


