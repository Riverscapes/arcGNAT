---
title: Sinousity by Segment
---


The **Sinousity by Segment** tool calculates a sinuosity value for each segment feature in a polyline feature class.

_______________________________________________________________
## Usage

### Input Parameters

**Input Stream Network or Centerline**

Segmented stream network or centerline polyline feature class. Sinuosity is calculated for each polyline feature.

**Sinousity Field Name**

Name of attribute field which will store calculated sinuosity values. Defaults to "Sinousity". 

**Save Temp Files to Scratch Workspace** (optional)

File geodatabase or folder for storing temporary data files that are generated during processing. If not specified, the workspace uses "in_memory" by default.

_______________________________________________________________
## Technical Background

### Calculation Method

1. Loop through each segment in the polyline feature class
2. Find straight line distance between segment end points
3. Divide segment length by straight line distance
4. Populate sinousity attribute field with calculated values.

### Troubleshooting and Potential Issues###