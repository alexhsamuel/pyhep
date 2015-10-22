from   hep.hist import Histogram, Histogram1D, project
import hep.table
import pickle

histograms = {
    "energy":   Histogram1D(20, (0.0, 5.0), "energy", "GeV",
                expression="energy"),

    "pt":       Histogram1D(20, (1.0, 3.0), "p_T", "GeV/c",
                expression="hypot(p_x, p_y)"),

    "mass":     Histogram1D(20, (0.0, 0.2), "mass", "GeV/c^2",
                expression="sqrt(energy**2 - p_x**2 - p_y**2 - p_z**2)"),

    "px_vs_py": Histogram((8, (-2.0, 2.0), "p_x", "GeV/c"),
                          (8, (-2.0, 2.0), "p_y", "GeV/c"),
                expression="p_x, p_y"),
    }

tracks = hep.table.open("tracks.table")
project(tracks.select("energy > 2.5"), histograms.values())
pickle.dump(histograms, file("histograms.pickle", "w"))
