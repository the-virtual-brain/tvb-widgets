

import bct
import numpy as np

def short_doc(doc):
    if not doc:
        return ""
    return doc.split("Parameters")[0].strip()

NETWORK_VECTOR_OVERRIDES = {
    ("kcoreness_centrality_bu", 1),
    ("kcoreness_centrality_bd", 1),
}

BCT_METRICS = {
    "ModularityOCSM": {
        "description": short_doc(bct.modularity_dir.__doc__),
        "func_name": "modularity_dir",
        "undirected": False,
        "fn": lambda c: bct.modularity_dir(c.weights),
        "labels": ["Optimal Community Structure", "Maximized Modularity"],
    },
    "ModularityOpCSMU": {
        "description": short_doc(bct.modularity_und.__doc__),
        "func_name": "modularity_und",
        "undirected": True,
        "fn": lambda c: bct.modularity_und(c.weights),
        "labels": ["Optimal Community Structure", "Maximized Modularity"],
    },
    "DistanceDBIN": {
        "description": short_doc(bct.distance_bin.__doc__),
        "func_name": "distance_bin",
        "undirected": False,
        "matrix_attr": "tract_lengths",
        "fn": lambda c: bct.distance_bin(c.tract_lengths),
        "labels": ["Distance matrix"],
    },
    "DistanceDWEI": {
        "description": short_doc(bct.distance_wei.__doc__),
        "func_name": "distance_wei",
        "undirected": False,
        "matrix_attr": "tract_lengths",
        "fn": lambda c: bct.distance_wei(c.tract_lengths),
        "labels": ["Distance matrix", "Number of edges in shortest path"],
    },
    "DistanceRDM": {
        "description": short_doc(bct.breadthdist.__doc__),
        "func_name": "breadthdist",
        "undirected": False,
        "matrix_attr": "tract_lengths",
        "fn": lambda c: bct.breadthdist(c.tract_lengths),
        "labels": ["Reachability matrix", "Distance matrix"],
    },
    "DistanceRDA": {
        "description": short_doc(bct.reachdist.__doc__),
        "func_name": "reachdist",
        "undirected": False,
        "matrix_attr": "tract_lengths",
        "fn": lambda c: bct.reachdist(c.tract_lengths),
        "labels": ["Reachability matrix", "Distance matrix"],
    },
    "DistanceNETW": {
        "description": short_doc(bct.findwalks.__doc__),
        "func_name": "findwalks",
        "undirected": False,
        "matrix_attr": "tract_lengths",
        "fn": lambda c: bct.findwalks(c.tract_lengths),
        "labels": ["Walk count tensor (per region pair, per path length)",
                   "Total number of walks found", "Walk length distribution"],
    },
    "CentralityNodeBinary": {
        "description": short_doc(bct.betweenness_bin.__doc__),
        "func_name": "betweenness_bin",
        "undirected": False,
        "fn": lambda c: bct.betweenness_bin(c.binarized_weights),
        "labels": ["Node Betweenness Centrality Binary"],
    },
    "CentralityNodeWeighted": {
        "description": short_doc(bct.betweenness_wei.__doc__),
        "func_name": "betweenness_wei",
        "undirected": False,
        "fn": lambda c: bct.betweenness_wei(c.weights),
        "labels": ["Node Betweenness Centrality Weighted"],
    },
    "CentralityEigenVector": {
        "description": short_doc(bct.eigenvector_centrality_und.__doc__),
        "func_name": "eigenvector_centrality_und",
        "undirected": True,
        "fn": lambda c: bct.eigenvector_centrality_und(c.weights),
        "labels": ["Eigenvector Centrality"],
    },
    "CentralityKCoreness": {
        "description": short_doc(bct.kcoreness_centrality_bu.__doc__),
        "func_name": "kcoreness_centrality_bu",
        "undirected": False,
        "fn": lambda c: bct.kcoreness_centrality_bu(c.binarized_weights),
        "labels": ["Node coreness (BU)", "Size of k-core"],
    },
    "CentralityKCorenessBD": {
        "description": short_doc(bct.kcoreness_centrality_bd.__doc__),
        "func_name": "kcoreness_centrality_bd",
        "undirected": False,
        "fn": lambda c: bct.kcoreness_centrality_bd(c.binarized_weights),
        "labels": ["Node coreness (BD)", "Size of k-core"],
    },
    "CentralityShortcuts": {
        "description": short_doc(bct.erange.__doc__),
        "func_name": "erange",
        "undirected": False,
        "fn": lambda c: bct.erange(c.binarized_weights),
        "labels": ["Edge Range", "Average Range (Eta)", "Shortcut Edges", "Fraction of Shortcuts"],
    },
    "FlowCoefficents": {
        "description": short_doc(bct.flow_coef_bd.__doc__),
        "func_name": "flow_coef_bd",
        "undirected": False,
        "fn": lambda c: bct.flow_coef_bd(c.binarized_weights),
        "labels": [
            "Flow coefficient for each node",
            "Average flow coefficient over the network",
            "Paths flowing across the central node",
        ],
    },
    "ParticipationCoefficent": {
        "description": short_doc(bct.participation_coef.__doc__),
        "func_name": "participation_coef",
        "undirected": False,
        "fn": lambda c: bct.participation_coef(c.weights, bct.modularity_dir(c.weights)[0]),
        "labels": ["Participation Coefficient"],
    },
    "ParticipationCoefficentSign": {
        "description": short_doc(bct.participation_coef_sign.__doc__),
        "func_name": "participation_coef_sign",
        "undirected": True,
        "fn": lambda c: bct.participation_coef_sign(c.weights, bct.modularity_dir(c.weights)[0]),
        "labels": [
            "Participation Coefficient (positive weights)",
            "Participation Coefficient (negative weights)",
        ],
    },
    "SubgraphCentrality": {
        "description": short_doc(bct.subgraph_centrality.__doc__),
        "func_name": "subgraph_centrality",
        "undirected": False,
        "fn": lambda c: bct.subgraph_centrality(c.binarized_weights),
        "labels": ["Subgraph Centrality"],
    },
    "ClusteringCoefficent": {
        "description": short_doc(bct.clustering_coef_bd.__doc__),
        "func_name": "clustering_coef_bd",
        "undirected": False,
        "fn": lambda c: bct.clustering_coef_bd(c.binarized_weights),
    },
    "ClusteringCoefficentBU": {
        "description": short_doc(bct.clustering_coef_bu.__doc__),
        "func_name": "clustering_coef_bu",
        "undirected": True,
        "fn": lambda c: bct.clustering_coef_bu(c.binarized_weights),
    },
    "ClusteringCoefficentWU": {
        "description": short_doc(bct.clustering_coef_wu.__doc__),
        "func_name": "clustering_coef_wu",
        "undirected": True,
        "fn": lambda c: bct.clustering_coef_wu(c.scaled_weights()),
    },
    "ClusteringCoefficentWD": {
        "description": short_doc(bct.clustering_coef_wd.__doc__),
        "func_name": "clustering_coef_wd",
        "undirected": False,
        "fn": lambda c: bct.clustering_coef_wd(c.scaled_weights()),
    },
    "TransitivityBinaryDirected": {
        "description": short_doc(bct.transitivity_bd.__doc__),
        "func_name": "transitivity_bd",
        "undirected": False,
        "fn": lambda c: bct.transitivity_bd(c.binarized_weights),
        "labels": ["Transitivity (Binary Directed)"],
    },
    "TransitivityWeightedDirected": {
        "description": short_doc(bct.transitivity_wd.__doc__),
        "func_name": "transitivity_wd",
        "undirected": False,
        "fn": lambda c: bct.transitivity_wd(c.scaled_weights()),
        "labels": ["Transitivity (Weighted Directed)"],
    },
    "TransitivityBinaryUndirected": {
        "description": short_doc(bct.transitivity_bu.__doc__),
        "func_name": "transitivity_bu",
        "undirected": True,
        "fn": lambda c: bct.transitivity_bu(c.binarized_weights),
    },
    "TransitivityWeightedUndirected": {
        "description": short_doc(bct.transitivity_wu.__doc__),
        "func_name": "transitivity_wu",
        "undirected": True,
        "fn": lambda c: bct.transitivity_wu(c.scaled_weights()),
    },
    "Degree": {
        "description": short_doc(bct.degrees_und.__doc__),
        "func_name": "degrees_und",
        "undirected": True,
        "fn": lambda c: bct.degrees_und(c.weights),
    },
    "DegreeIOD": {
        "description": short_doc(bct.degrees_dir.__doc__),
        "func_name": "degrees_dir",
        "undirected": False,
        "fn": lambda c: bct.degrees_dir(c.weights),
        "labels": ["Node indegree", "Node outdegree", "Node degree (indegree + outdegree)"],
    },
    "MatchingIndex": {
        "description": short_doc(bct.matching_ind.__doc__),
        "func_name": "matching_ind",
        "undirected": False,
        "fn": lambda c: bct.matching_ind(c.weights),
        "labels": [
            "Matching index — incoming connections",
            "Matching index — outgoing connections",
            "Matching index — all connections",
        ],
    },
    "Strength": {
        "description": short_doc(bct.strengths_und.__doc__),
        "func_name": "strengths_und",
        "undirected": False,
        "fn": lambda c: bct.strengths_und(c.weights),
    },
    "StrengthISOS": {
        "description": short_doc(bct.strengths_dir.__doc__),
        "func_name": "strengths_dir",
        "undirected": False,
        "fn": lambda c: bct.strengths_dir(c.weights),
    },
    "StrengthWeights": {
        "description": short_doc(bct.strengths_und_sign.__doc__),
        "func_name": "strengths_und_sign",
        "undirected": False,
        "fn": lambda c: bct.strengths_und_sign(c.weights),
        "labels": ["Positive Strength", "Negative Strength", "Total Positive Weight", "Total Negative Weight"],
    },
    "DensityDirected": {
        "description": short_doc(bct.density_dir.__doc__),
        "func_name": "density_dir",
        "undirected": False,
        "fn": lambda c: bct.density_dir(c.weights),
        "labels": ["Density", "Number of Nodes", "Number of Edges"],
    },
    "DensityUndirected": {
        "description": short_doc(bct.density_und.__doc__),
        "func_name": "density_und",
        "undirected": True,
        "fn": lambda c: bct.density_und(c.weights),
    },
}

ANALYZER_GROUPS = {
    "Modularity": ["ModularityOCSM", "ModularityOpCSMU"],
    "Distance"  : ["DistanceDBIN", "DistanceDWEI", "DistanceRDM", "DistanceRDA", "DistanceNETW"],
    "Centrality": ["CentralityNodeBinary", "CentralityNodeWeighted", "CentralityEigenVector", "CentralityKCoreness", "CentralityKCorenessBD", "CentralityShortcuts", "FlowCoefficents", "ParticipationCoefficent", "ParticipationCoefficentSign", "SubgraphCentrality"],
    "Clustering": ["ClusteringCoefficent", "ClusteringCoefficentBU", "ClusteringCoefficentWU", "ClusteringCoefficentWD", "TransitivityBinaryDirected", "TransitivityWeightedDirected", "TransitivityBinaryUndirected", "TransitivityWeightedUndirected"],
    "Degree and Similarity": ["Degree", "DegreeIOD", "MatchingIndex", "Strength", "StrengthISOS", "StrengthWeights"],
    "Density": ["DensityDirected", "DensityUndirected"],
}