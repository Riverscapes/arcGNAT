The **Find Crossing Lines** tool looks for places where the input stream network has more than three stream reaches converging at one location.  It creates a one meter buffer at each location.  The user can then manually edit one of the stream reach line features to fall outside the one meter buffer.

## Usage

### Parameters

**Input Stream Network** 

The feature class to be processed. This should be a projected stream network.

**Output Workspace:**

A folder or geodatabase where the resulting polygon feature class will be created.

**Output Polygon Name:**

A name you create for the buffer feature class output by this script.  This fill will be created in the Output Workspace.

**Scratch Workspace:**

The folder or geodatabase where you want the working files to be created.

### Outputs

**Output Polygon**

Each Polygon Feature in this dataset represents a location in the stream network where more than 3 lines intersect (i.e two line features cross, rather than converge).

## Technical Background

### Calculation Method