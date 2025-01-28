import pandas as pd
import time
from graph import Graph

def main():

    # dir paths
    # ---------
    # (michael)
    amp_repo_datasets_dir = "/Users/michael/Downloads/amplicon_repo_datasets/"
    gene_alias_path = "/Users/michael/Documents/GitHub/ecdna-coamp/graph-constructor/data/coamp_gene_mapper_12.21.24.tsv"

    # (kyra)
    # amp_repo_datasets_dir = "/mnt/c/Users/Owner/OneDrive/Documents/BENG_Senior_Design/DepMap/data/"
    
    # (dhruv)
    # amp_repo_dir = ""
    
    # import datasets
    # ---------------
    ccle = pd.read_csv(amp_repo_datasets_dir + "ccle_aggregated_results.csv")
    # pcawg = pd.read_csv(amp_repo_datasets_dir + "pcawg_aggregated_results.csv")
    # tcga = pd.read_csv(amp_repo_datasets_dir + "tcga_aggregated_results.csv")
    # aggregated = pd.concat([ccle, pcawg, tcga])

    aliasdf = pd.read_csv(gene_alias_path, sep='\t')
    alias_dict = pd.Series(aliasdf['DepMapGeneName'].values, index=aliasdf['GeneName']).to_dict()

    # build ccle graph
    start = time.process_time()

    print("CCLE GRAPH")
    print("-----------")
    graph = Graph(dataset=ccle)
    
    print("Nodes:", graph.NumNodes())   # 3320
    print(" Edges:", graph.NumEdges())  # 118033

    graph.Nodes_df().to_csv('test_nodes.csv', index=False)  
    graph.Edges_df().to_csv('test_edges.csv', index=False)  

    end = time.process_time()
    print("Export graph:", end - start, " seconds")

if __name__ in "__main__":
    main()