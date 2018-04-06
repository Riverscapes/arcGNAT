"""Moving Window for GNAT"""

import math
import arcpy
from lib import gis_tools

__version__ = "0.0.2"


def main(fcLineNetwork,
         fieldStreamRouteID,
         seed_distance,
         window_sizes,
         stat_fields,
         fcOutputWindows,
         fcOutputSeedPoints,
         tempWorkspace=arcpy.env.scratchWorkspace):
    """Perform a Moving Window Analysis on a Line Network."""

    # Prepare Inputs
    arcpy.AddMessage("Preparing Moving Window Analysis")
    fc_line_dissolve = gis_tools.newGISDataset(tempWorkspace, "GNAT_MWA_LineNetworkDissolved")
    arcpy.Dissolve_management(fcLineNetwork, fc_line_dissolve, fieldStreamRouteID, multi_part=False, unsplit_lines=True)
    #listWindows = []
    listSeeds = []
    #listWindowEvents = []
    listgWindows = []
    intSeedID = 0

    # Moving Window Generation
    arcpy.AddMessage("Starting Window Generation")
    iRoutes = int(arcpy.GetCount_management(fc_line_dissolve).getOutput(0))
    arcpy.SetProgressor("step", "Processing Each Route", 0, iRoutes, 1)
    iRoute = 0
    with arcpy.da.SearchCursor(fc_line_dissolve, ["SHAPE@", fieldStreamRouteID, "SHAPE@LENGTH"]) as scLines:
        for fLine in scLines:  # Loop Through Routes
            arcpy.SetProgressorLabel("Route: {} Seed Point: {}".format(iRoute, intSeedID))
            arcpy.SetProgressorPosition(iRoute)
            gLine = fLine[0]
            dblSeedPointPosition = float(max(window_sizes)) / 2  # Start Seeds at position of largest window
            while dblSeedPointPosition + float(max(window_sizes)) / 2 < fLine[2]:
                arcpy.SetProgressorLabel("Route: {} Seed Point: {}".format(iRoute, intSeedID))
                gSeedPointPosition = gLine.positionAlongLine(dblSeedPointPosition)
                listSeeds.append([scLines[1], intSeedID, gSeedPointPosition])
                for window_size in window_sizes:
                    dblWindowSize = float(window_size)
                    dblLengthStart = dblSeedPointPosition - dblWindowSize / 2
                    dblLengthEnd = dblSeedPointPosition + dblWindowSize / 2

                    #gPointStartLocation = gLine.positionAlongLine(dblLengthStart)
                    #gPointEndLocation = gLine.positionAlongLine(dblLengthEnd)
                    listgWindows.append([scLines[1], intSeedID, dblWindowSize, gLine.segmentAlongLine(dblLengthStart, dblLengthEnd)])
                    #listWindows.append([scLines[1], intSeedID, dblWindowSize, gPointStartLocation])
                    #listWindows.append([scLines[1], intSeedID, dblWindowSize, gPointEndLocation])
                    #listWindowEvents.append([scLines[1], intSeedID, dblWindowSize, dblLengthStart, dblLengthEnd])
                dblSeedPointPosition = dblSeedPointPosition + float(seed_distance)
                intSeedID = intSeedID + 1
            iRoute = iRoute + 1

    arcpy.AddMessage("Compiling Moving Windows")
    fcSeedPoints = gis_tools.newGISDataset(tempWorkspace, "GNAT_MWA_SeedPoints")
    #fcWindowEndPoints = gis_tools.newGISDataset(tempWorkspace, "GNAT_MWA_WindowEndPoints")
    fcWindowLines = gis_tools.newGISDataset(tempWorkspace, "GNAT_MWA_WindowLines")

    arcpy.CreateFeatureclass_management(tempWorkspace, "GNAT_MWA_SeedPoints", "POINT", spatial_reference=fcLineNetwork)
    # arcpy.CreateFeatureclass_management(tempWorkspace, "GNAT_MWA_WindowEndPoints", "POINT",
    #                                     spatial_reference=fcLineNetwork)
    arcpy.CreateFeatureclass_management(tempWorkspace, "GNAT_MWA_WindowLines", "POLYLINE",
                                        spatial_reference=fcLineNetwork)

    gis_tools.resetField(fcSeedPoints, "RouteID", "TEXT")
    gis_tools.resetField(fcSeedPoints, "SeedID", "LONG")

    # gis_tools.resetField(fcWindowEndPoints, "RouteID", "TEXT")
    # gis_tools.resetField(fcWindowEndPoints, "SeedID", "LONG")
    # gis_tools.resetField(fcWindowEndPoints, "Seg", "DOUBLE")

    gis_tools.resetField(fcWindowLines, "RouteID", "TEXT")
    gis_tools.resetField(fcWindowLines, "SeedID", "LONG")
    gis_tools.resetField(fcWindowLines, "Seg", "DOUBLE")

    with arcpy.da.InsertCursor(fcSeedPoints, ["RouteID", "SeedID", "SHAPE@XY"]) as icSeedPoints:
        for row in listSeeds:
            icSeedPoints.insertRow(row)

    # with arcpy.da.InsertCursor(fcWindowEndPoints, ["RouteID", "SeedID", "Seg", "SHAPE@XY"]) as icWindowEndPoints:
    #     for row in listWindows:
    #         icWindowEndPoints.insertRow(row)

    with arcpy.da.InsertCursor(fcWindowLines, ["RouteID", "SeedID", "Seg", "SHAPE@"]) as icWindowLines:
        for row in listgWindows:
            icWindowLines.insertRow(row)

    # Intersecting Network Attributes with Moving Windows
    arcpy.AddMessage("Intersecting Network Attributes with Moving Windows")
    fcIntersected = gis_tools.newGISDataset(tempWorkspace, "GNAT_MWA_IntersectWindowAttributes")
    arcpy.Intersect_analysis([fcWindowLines, fcLineNetwork], fcIntersected, "ALL", output_type="LINE")

    # Use Python Dictionaries for Summary Stats
    # Reference: https://community.esri.com/blogs/richard_fairhurst/2014/11/08/turbo-charging-data-manipulation-with-python-cursors-and-dictionaries
    arcpy.AddMessage("Loading Moving Window Attributes")
    valueDict = {}
    with arcpy.da.SearchCursor(fcIntersected, ["SeedID", "Seg", "SHAPE@LENGTH"] + stat_fields) as searchRows:
        for searchRow in searchRows:
            keyValue = str(searchRow[0])
            segValue = str(searchRow[1])
            if not keyValue in valueDict:
                valueDict[keyValue] = {segValue: [(searchRow[2:])]}
            else:
                if segValue not in valueDict[keyValue]:
                    valueDict[keyValue][segValue] = [(searchRow[2:])]
                else:
                    valueDict[keyValue][segValue].append((searchRow[2:]))

    addfields = ["w{}{}_{}".format(str(ws)[:2], stat, field)[:10] for ws in window_sizes for field in stat_fields for stat in ["N", "Av", "Sm", "Rn", "Mn", "Mx", "Sd", "WA"]]
    for field in addfields:
        gis_tools.resetField(fcSeedPoints, field, "DOUBLE")

    arcpy.AddMessage("Calculating Attribute Statistics")
    with arcpy.da.UpdateCursor(fcSeedPoints, ["SeedID"] + addfields) as ucSeedPoints:
        for row in ucSeedPoints:
            new_row = [row[0]]
            for ws in window_sizes:
                seglen = [segment[0] for segment in valueDict[str(row[0])][str(ws)]]
                for i in range(1, len(stat_fields) + 1):
                    vals = [float(segment[i]) for segment in valueDict[str(row[0])][str(ws)]]
                    count_vals = float(len(vals))
                    sum_vals = sum(vals)
                    ave_vals = sum_vals / float(count_vals)
                    max_vals = max(vals)
                    min_vals = min(vals)
                    range_vals = max_vals - min_vals
                    sd_vals = math.sqrt(sum([abs(float(x) - float(ave_vals))**2 for x in vals]) / float(count_vals))
                    wave_vals = sum([val / slen for val, slen in zip(vals, seglen)])/ float(count_vals)
                    new_row.extend([count_vals, ave_vals, sum_vals, range_vals, min_vals, max_vals, sd_vals, wave_vals])
            ucSeedPoints.updateRow(new_row)

    # stat_fields_param = [[field, stat] for field in stat_fields for stat in ["COUNT", "MEAN", "SUM", "RANGE", "MIN", "MAX", "STD"]]
    # stats = gis_tools.newGISTable(tempWorkspace, "StatisticsTable")
    # arcpy.Statistics_analysis(fcIntersected, stats, stat_fields_param, ["SeedID", "Seg"])

    #arcpy.JoinField_management(fcSeedPoints, "SeedID", stats, "SeedID")

    # Manage Outputs
    arcpy.AddMessage("Saving Outputs")
    gis_tools.resetData(fcOutputSeedPoints)
    arcpy.CopyFeatures_management(fcSeedPoints, fcOutputSeedPoints)
    gis_tools.resetData(fcOutputWindows)
    arcpy.CopyFeatures_management(fcWindowLines, fcOutputWindows)

    return 0


if __name__ == "__main__":

    pass
    #todo add argparse
    # main(
    #     sys.argv[1],
    #     sys.argv[2],
    #     sys.argv[3],
    #     sys.argv[4],
    #     sys.argv[5],
    #     sys.argv[6],
    #     sys.argv[7],
    #     sys.argv[8])