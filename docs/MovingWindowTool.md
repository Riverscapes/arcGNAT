---
title: Moving Window Analysis
---

The moving window analysis tool summarizes attributes on length based 'windows' centered around 'seed points'. 

![]()

# Usage

![](Images/MovingWindowToolWindow.PNG)

1. The Moving Window Summary requires a Stream Branch or similar field to identify tributary routing. The moving window can summarize numeric data fields only.
2. In ArcMap navigate to Geomorphic Network and Analysis Toolbox / Utilities / Moving Window Summary in ArcToolbox.
   1. Specify the **Stream Network Polyline Feature Class** to run the summary over.
   2. Specify a **Stream name or Branch Field** that is used to make continuous stretches of the stream. For Example, GNAT uses a "Stream Branch ID" system. 
   3. Specify the **Seed Point Distance** to use for spacing the seed points along the network. Seed points will start at 1/2 the distance of the largest window size in order to retain all window sizes for every seed point.
   4. Specify the window size(s) you want to use. Each window size will provide a summary at each seed point.
   5. Specify the Attribute Fields that will be used to **Calculate Statistics**. Numeric (Float, Double or Integer types only).
   6. Specify the output **Moving Windows** and **Seed Point** Feature classes .
   7. (Optional) specify a Temporary workspace. If one is not specified, the "in_memory" workspace will be used.
   8. (Optional) Specify Riverscapes project and outputs.
   9. Click OK to run the tool.

# Parameters

## Inputs ##

### Line Network

The Line network on which the Moving Window analysis will be generated. ****

Requirements: 

* Contains the network attributes for which the moving window summary will be calculated. 
* The Line Network must have tributary topology information as an attribute to dissolve the network (i.e. GNIS names, Stream Order, etc)

### Stream Route ID

The field that contains a unique ID for each Stream/Route. The tool will dissolve based on this ID, so as to create the longest continuous river segments for generating the Seed Points.

### Seed Point Distance

Distance between seed points. Seed Points represent the center of each window, and multiple windows are aligned on each seed point. The first seed point is located at half the distance of the largest window size from the ends of each stream route. This is to ensure that each seed point has every window size associated with it.

### Window Sizes

Window size (in meters) to be generated at each seed point.  Multiple window sizes can be specified.

### Generate Statistics Fields

Select the fields to generate statistics on. Only Numeric (Float, Double Integer) types are allowed.

## Outputs ##

In the output workspace you will find:

### Seed Points

Points feature class that contain the calculated attribute for each window size, centered on each seed point feature. This layer contains the following attributes:

* `RouteID`: The same attribute as the `StreamBranchID` specified in the inputs.
* `SeedID`: Unique ID for each seed point. Can be used to join back to Window line features in Moving Window Lines.
* Attribute summaries will saved in fields that are named using the following structure `wXXSS_ATRB`:
  * `wXX` The first part of the field name contains "w" followed by the first two digits fo the window size. 
  * `ST_` Statistics Type:
    * `N` Count
    * `Av` Average
    * `Sm` Sum
    * `Rn` Range
    * `Mn` Minimum Value
    * `Mx` Maximum Value
    * `Sd` Standard Deviation
    * `WA` Weighted Average (by length of segment)
  * `ATRB` The first few letters of the original attribute field for that statistic generated. 

### Moving Window Lines

The line features that represent the moving windows. These features will overlap both in window spacing (seed distance) and window sizes. This layer contains the following attributes:

* `SeedID`: Unique id for each seed point. This can be used to join back to the individual seed points.
* `Window size`: Size of the window (due to geometric rounding, the actual shape length may be slightly larger or smaller than the window size).

## Methods

1. Line Network is dissolved by user specified "StreamRoute" Field.
2. Iterate through each Stream Route
   1. Generate Seed Points starting at a distance of 1/2 largest window size, using a spacing distance as provided by user.
   2. for each seed point:
      1. For each window size provided by user, 
         1. find the upper distance and lower distance of window centered on the seed point.
         2. Use the distances to find segment along line (arcpy geometry method)
3. Generate Feature classes of Seed Points and windows
4. Intersect the Windows with the Original Line network.
5. Read the Intersected Line Network into Python Dictionaries
6. Add new fields to store calculated statistics to Seed Points
7. Calculate statistics for each statistic type for each attribute, for each seed and window size .
8. Save outputs to user specified destinations.

# About

- **Code Repository** https://github.com/Riverscapes/arcGNAT
- **Software Architecture** Python 2.7 with standard library and the following 3rd-Party Dependencies:
  - arcpy
- **ArcGIS** version 10.4 or higher.
- Code for this tool written and maintained by Kelly Whitehead at South Fork Research.

# Release Notes

- `version 0.0.2` 2018-04-05
  - Use Python Dictionaries and Cursors to generate statistics instead of arcpy Summary Statistics tool.
- `version 0.0.1`  2018-03-28
  - Tool initialized.

[TOOL HOME](index.md)