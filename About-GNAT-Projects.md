The concepts here are based on the two-step process for generating a confinement Project. 

![](https://docs.google.com/drawings/d/1Y2zYp1tdWn-FWincxK55xr-zfW4yJCfg7Nw4UEpONRk/pub?w=1326&h=722)

## GNAT Project

MetaData

- Region
- Watershed
- User/Operator

### Inputs

The only input for a GNAT project is a stream network dataset.

MetaData

- Source or type (NHD+ V02, 
- Scale?

### Realization

A GNAT realization represents steps 1 and 2 in the current GNAT workflow.
 
1. Initial Network Topology table is generated 
2. Network features and errors are identified
3. Network topology errors are fixed (manually in GIS software).
4. Return to step 1 and repeat as needed.

Params

-

Metadata

- Editing Notes

Outputs

- GNAT network polyline feature class
- GNAT network topology table

### Analyses

An "Analysis" represents a segmented or stream branch processed network. These can be input into other geomorphic attribute projects as inputs. Several Analyses can be associated with a Realization, but if the Realization changes or is updated, new analyses must be generated for that Realization.

#### Segmented Network

Network polyline feature class split by segments with original attributes retained. Segmentation is identified by a `SegmentID` Field.

Parameters

- SegID Field
- Pre-Segmentation Dissolve Options (None, Stream Branches)
- Segmentation Distance
- Segmentation Direction ("Move Upstream", "Move Downstream")
- Segmentation Remainder Option ("End","Proportional")

Outputs

- Segmented GNAT network polyline feature class
- GNAT network table

#### Stream Branch

Network polyline feature class with a stream branch ID field applied. Original attributes are retained.

- GNAT network polyline feature class with stream branch identifiers
- GNAT network table

#### Other Analysis types?

Are there other types of analyses here? I also think it is possible to have a project just link to the realization and not a specific analysis. 

## Workflow
The following is a proposed workflow for using GNAT in project Mode. The main issue is that Network prep has some cyclical and manual steps, so a realization does not appear until the user commits the updates.

1. Project Management (Toolset level)
   1. New GNAT Project
      + Creates XML
      + Project Meta
   2. Load Raw Network to Project
      + Copies Line Network to Inputs
2. Main/Step 1 - Network Prep
   1. Generate Topology Table
      + Generates Companion Topology Table
      + **Does not output to Realization**
   2. Generate Network Features/Errors
      + Uses table and network geometry to find attributes
      + **Does not output to Realization**
   3. (Manual) Repair network errors
      + Manual Step
      + Repeat step 1 and 2 after this
   4. Commit Network
      + User Names Realization
      + Copies Network and Table to Realization Level of Project (Outputs/RealizationName/Network)
3. Step 2 - Network Segments
   1. Segmentation Tool
      + Applies segmentation to network (as segID)
      + Keeps original Attributes (Need to retain some type of Original ReachID)
      + Save at Analysis level (Outputs/RealizationName/Analyses/AnalysisName)
4. Step 3 - Geomorphic Attributes
   + This probably represents a separate project?

## Example Project File

[Example XML](https://gist.github.com/KellyMWhitehead/8a198d59ed3e1df69c4c39733e865327)