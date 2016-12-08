The **Generate Stream Branches** tool dissolves the line network based on GNIS name and stream order attributes, to create stream branches in the stream network polyline feature class. The resulting stream branches can then by used by the **Segment Stream Network** tool for splitting the stream network by the longest, continuous stretches of stream.

___
## Usage

> For the entire Stream Branch workflow, see [Stream Network and Segmentation](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Workflow/StreamNetworkandSegmentation)

### Parameters
 
**Input Stream Network** (with Stream Order)

Stream network with Stream Order Attributes (from stream order tool). 

**Input Junction Points** (Optional)

Use the Junction Points Output from the Stream Order tool to split branches at Stream Order Convergences. Otherwise, the tool will dissolve all stream order segments that converge with the same stream order value.

**Stream Name Field**

Attribute Field with GNIS_Stream Name. Not all segments need to have a stream name - the tool will use Stream Order for segments without a stream name.

**Stream Order Field**

Attribute Field that contains the Stream Order for each line feature.

**Output Line Network with Branch ID**

File GDB polyline feature class. The tool will overwrite existing dataets. 


**Dissolve Output by BranchID?** (Optional)

* `Checked`: The output stream network will contain all features dissolved by the BranchID. Feature Attributes will be dropped due to the dissolve.

* `Unchecked`: The output stream network will retain its original features and attributes, with the addition of the `BranchID` field.

**Scratch Workspace** (Optional)

You may use:

1. Create a new file GDB to save temporary processing files (useful for debugging).
3. If a workspace is not designated, the tool will use the "in_memory" workspace. You will not be able to view the temporary files, _but the processing speed will be much faster_.

____
## Technical Background

This tool uses the following methodology:

1. Input Line Features are selected by GNIS_name, then Dissolved by GNIS_name.
2. The Selection is switched, then Dissolved by Stream Order, if present
3. The Outputs from 2 and 3 are merged.
5. Split Line at Point using the input Junction Points
	> This fixes the issue where two tributaries with the same stream order (and no GNIS) are dissolved together. This mainly occurs at the headwaters (i.e. Stream order = 1).
5. Add a unique Id field (`BranchID`) to identify each branch
6. The Original input is intersected with the Branches layer, if the output is not to be dissolved. Otherwise, the output is simply copied over from the Branches layer.
