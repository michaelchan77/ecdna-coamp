import time
import pandas as pd
from GraphClass import Graph
from NodeClass import Node
import py4cytoscape as py4

def main():

    # # test Cytoscape connection
    # print(dir(py4))
    # print(py4.cytoscape_ping())
    # print(py4.cytoscape_version_info())

    # paths
    # -----
    # michael
    small_test_path = "/Users/michael/Documents/GitHub/ecdna-depmap/frequency-graph/data/small_dataset.csv"
    ccle_path = "/Users/michael/Downloads/amplicon_repo_datasets/ccle_aggregated_results.csv"
    pcawg_path = "/Users/michael/Downloads/amplicon_repo_datasets/pcawg_aggregated_results.csv"
    tcga_path = "/Users/michael/Downloads/amplicon_repo_datasets/tcga_aggregated_results.csv"
    oncogene_path = "/Users/michael/Documents/GitHub/ecdna-depmap/frequency-graph/data/oncogene_list_hg38.txt"
    # # dhruv
    # small_test_path = "AA_aggregated_results_small_example.csv"
    # # kyra
    # small_test_path = "/Users/Owner/Documents/GitHub/ecdna-depmap/frequency-graph/data/small_dataset.csv"

    # import datasets
    # ---------------
    small_test = pd.read_csv(small_test_path) 
    ccle = pd.read_csv(ccle_path) # missing [AA directory] and [cnvkit directory] columns
    pcawg = pd.read_csv(pcawg_path)
    tcga = pd.read_csv(tcga_path)
    aggregated = pd.concat([ccle, pcawg, tcga])
    with open (oncogene_path) as f:
        oncogenes = f.read().splitlines()
    
    # build, print, export graph for small dataset
    # -----------
    if 0:
        print("SMALL GRAPH")
        print("-----------")
        small_graph = Graph(small_test, oncogene_list=oncogenes, threshold=0)
        print("Num Edges:", small_graph.NumEdges())
        small_graph.Print()
        # small_graph.Export("small_graph.tsv")
        print("-----------\n")

    # a v bcd sig genes subgraph testing
    if 0:
        print("CCLE GRAPH")
        print("-----------")
        graph = Graph(ccle, oncogene_list=oncogenes)
        genelistpath = "/Users/michael/Documents/GitHub/ecdna-depmap/frequency-graph/data/sig_genes_a-bcd_2024q2.txt"
        with open (genelistpath) as f:
            genelist = f.read().splitlines()
        print(genelist)
        subgraph = graph.Subgraph(genelist)
        subgraph.Print()
        subgraph.Export("a-bcd.tsv", "a-bcd_nodes.tsv")
        print("-----------\n")
    
    # ccle graph
    if 1:
        print("CCLE GRAPH")
        print("-----------")
        graph = Graph(ccle, oncogene_list=oncogenes)
        # print("Nodes:", graph.NumNodes(), " Edges:", graph.NumEdges())
        # Nodes: 3320  Edges: 118033
        graph.Export("neo4j_ccle_edges.csv", "neo4j_ccle_nodes.csv")
        print("-----------\n")

    # test aggregated dataset
    # -----------
    if 0:
        # build and export
        start = time.process_time()
        aa_graph = Graph(aggregated)
        print("Edges:", aa_graph.NumEdges(), "Nodes:", aa_graph.NumNodes())
        aa_graph.Export("aa_graph_1.tsv")
        end = time.process_time()
        print("Export graph:", end - start, " seconds")

        # # num edges for varying threshold values
        # for x in range(0,10):
        #     aa_graph = Graph(aggregated, threshold=x/10)
        #     print("Threshold:", x/10, "Edges:", aa_graph.NumEdges())
        # # Threshold: 0.0 Edges: 417242
        # # Threshold: 0.1 Edges: 341605
        # # Threshold: 0.2 Edges: 235321
        # # Threshold: 0.3 Edges: 190376
        # # Threshold: 0.4 Edges: 139582
        # # Threshold: 0.5 Edges: 89343
        # # Threshold: 0.6 Edges: 86592
        # # Threshold: 0.7 Edges: 78218
        # # Threshold: 0.8 Edges: 73943
        # # Threshold: 0.9 Edges: 72677

    # Read testing
    # -----------
    if 0:
        graph1 = Graph()
        graph1.Read("graph_original.tsv")
        graph1.Export()

    # Subgraph testing
    # -----------
    if 0: # passed
        tests = [ [],
                  ["CASC15"],
                  ["CASC15", "MTSS1", "ARPC4"],
                  ["CASC15", "MTSS1", "ATP2B2-IT2", "E2F3"],
                  ["CDKAL1", "ARPC4"]
        ]
        
        for list in tests:
            print(list)
            print("-----------")
            small_graph.Print(small_graph.Subgraph(list)) 
            print("-----------\n")  

    # CC testing
    # -----------
    if 0: # passed small graph
        print("TEST CC")
        print("-----------")

        # generate connected components
        cycles = small_graph.CC()

        # pretty print cycles
        for i in range(0, len(cycles)):
            print("Cycle", i, ":", end = " ")
            for node in cycles[i]:
                print(node.GetLabel(), end = " ")

        print("\n-----------\n")

    # Node class testing
    # -----------
    if 0: # passsed
        print("TEST NODE CLASS")
        print("-----------")
        node1 = Node("test_gene1", ["sample1"])
        node2 = Node("test_gene2")

        # test constructor, GetLabel, GetLocs, and AddLoc
        print("node1 label (expect \"test_gene1\"):", node1.GetLabel())
        print("node2 label (expect \"test_gene2\"):", node2.GetLabel())
        print()
        print("node1 sample list (expect [\"sample1\"]):", node1.GetLocs())
        print("node2 sample list (expect []):", node2.GetLocs())
        node2.AddLoc("sample2")
        print("add a sample to node2 locs:")
        print("node2 sample list (expect [\"sample2\"]):", node2.GetLocs())

        # test Intersect and Union
        node1.AddLoc("sample3")
        node1.AddLoc("sample4")
        node2.AddLoc("sample4")
        node2.AddLoc("sample5")

        print("intersection (expect [\"sample4\"]):", node1.Intersect(node2))
        print("union (expect [\"sample1\", \"sample2\", \"sample3\", \"sample4\", \"sample5\"]):", node1.Union(node2))

        print("-----------\n")

if __name__ in "__main__":
    main()