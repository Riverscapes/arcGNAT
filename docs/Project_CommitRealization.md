---
title: Commit Realization
---


The **Commit Realization** tool accepts a stream network polyline feature class and "commits" it to a GNAT Riverscape 
project. This commital initiates a new project *Realization*. A project *Realization* represents a specific version or 
snapshot of a stream network.  Multiple *Realizations* can be commited to a Riverscapes project, as long as each *Realization's*
stream network is unique, i.e the result of specific manual edits, attribute queries, or spatial extents.

_______________________________________________________________

## Usage

### Input Parameters

![commit_stream_example]({{site.baseurl}}/images/commit_stream_form.PNG)

**Realization Name**

* The name of the new *Realization* which will be added to GNAT Riverscape project. This name should be unique, and not
a replicate of any existing *Realization* within the project.

**Input Stream Network**

* A polyline feature class representing a unique version of a stream network. This network should be the result of a
a specific set of spatial or attribute queries and/or manual edits.

**Unique Reach ID Field** (optional)

* An attribute field of the input stream network polyline feature class that stores unique identifier values. 

**Network Table** (optional)

A table which store stream network topology data. This table should be the result of running the [Build Network Topology
Table](Build-Network-Topology-Table) tool

### Riverscapes Project Management

**GNAT Project XML** (optional)

* The XML file (*project.rs.xml*) which stores information on the associated Riverscapes project.