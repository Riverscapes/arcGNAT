---
title: Riverscapes Projects
---

ArcGNAT tools are structured in a way to enable the creation and organization of a [Riverscapes](https://github.com/riverscapes) Project. This allows the tools to organize project data and structure multiple versions of model outputs. 

# General GNAT Project Structure

The GNAT project consists of a `project.rs.xml` file that sits at the base of the folder.

##Project MetaData

ArcGNAT project contain at least the following metadata elements:

- Region
- Watershed
- User/Operator

## Inputs

The primary input for a GNAT project is the original stream network dataset used for the project, though additional inputs such as Valley Bottom Polygons, DEMs or Centerlines may be included depending on the Geomorphic and Attribute Analyses that are generated.

**Folder Structure** `/Inputs/StreamNetworks/StreamNetwork###/`

## Realization

A GNAT realization represents steps 1 and 2 in the current GNAT *Analyze Network Attributes* workflow.
 
1. Initial Network Topology table is generated 
2. Network features and errors are identified
3. Network topology errors are fixed (manually in GIS software).
4. Return to step 1 and repeat as needed.
5. Once the network data is cleaned, it may be 'committed' to a realization, from which network analyses can be generated. If the network needs further editing or revising, a new committed network realization must be generated (networks that are committed to a realization should not be edited to maintain data workflow integrity). 

**Folder Structure** `/Outputs/RealizationName`

***Realization Metadata***

- Editing Notes: Manually entered text provided by the user.

**Reazlation Outputs***

- GNAT network polyline feature class
- GNAT network topology table

## Network Analyses

An "Analysis" represents a segmented or stream branch processed network. These can be input into other geomorphic attribute projects as inputs. Several Analyses can be associated with a Realization, but if the Realization changes or is updated, new analyses must be generated for that Realization.

**Folder Structure** `/Outputs/RealizationName/Analyses/AnalysisName`

### Segmented Network

Network polyline feature class split by segments with original attributes retained. Segmentation is identified by a `SegmentID` Field.

***Parameters***

- SegID Field
- Pre-Segmentation Dissolve Options (None, Stream Branches)
- Segmentation Distance
- Segmentation Direction ("Move Upstream", "Move Downstream")
- Segmentation Remainder Option ("End","Proportional")

***Outputs***

- Segmented GNAT network polyline feature class
- GNAT network table

### Stream Branch

Network polyline feature class with a stream branch ID field applied. Original attributes are retained.

- GNAT network polyline feature class with stream branch identifiers
- GNAT network table

## Attribute Analyses

A further set of analyses can be generated from a Network Analysis, which represent geomorphic or network metrics calcultated from the Network.

**Folder Structure** `/Outputs/RealizationName/Analyses/AnalysisName` (Attributes are added to existing network datasets, so no additional files are genreated)

### Sinuosity Analysis
Adds a sinuosity calculation in a field named `C_Sin` to Network Analysis dataset.

### Planform Analysis
Adds a planform calculation in a field named `V_Plan` to Network Analysis dataset.

### Gradient Analysis
Adds a gradient calculation in a field named `Grad` to Network Anaysis dataset.

### Threadedness Analysis
Adds a threadedness calculation in a field named `--` to Network Analysis dataset.


## Project Workflow
The following is a proposed workflow for using GNAT in project Mode. Note that the Network prep step has some cyclical and manual processing, so a realization does not appear until the user commits the updates.

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
   + 

## Example Project File

[Example XML](https://gist.github.com/KellyMWhitehead/8a198d59ed3e1df69c4c39733e865327)
