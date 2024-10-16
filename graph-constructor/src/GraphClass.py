import csv
import re
import pandas as pd
from NodeClass import Node


class Graph:


	def __init__(self, dataset=None, oncogene_list=None, amp_type="ecDNA", loc_type="feature", threshold=0): # Michael
		"""
		Parameters:
			self (Graph) : Graph object 
			amp_type (str) : type of focal amplification (ecDNA, BFB, etc.)
			loc_type (str) : sample or feature
			dataset (tsv file) : AA aggregated results file
			threshold : min edge weight to include in Graph
		Return:
			None
		"""
		self.amp_type = amp_type
		self.loc_type = loc_type
		self.threshold = threshold
		self.graph = {}
		self.nodelist = []
		self.number_edges = 0
		if dataset is None:
			print("Read in Graph")	
		else:
			self.BuildGraph(dataset, oncogene_list)

	def SetThreshold(self, num):
		self.threshold = num

	def ExtractGenes(self, input):
		"""
		Parameters: 
			input (str) : ['A', 'B', 'C'] or ["'A'", "'B'", "'C'"]
		Return: 
			list: ["A", "B", "C"]
		"""
		pattern = r"['\"]?([\w-]+)['\"]?"
		genelist = re.findall(pattern, input)
		return genelist

	def BuildGraph(self, dataset, oncogene_list): # Dhruv
		"""
		Build a frequency graph based on a given dataset (AA agg results)
	
		Parameters: 
			self (Graph) : Graph object 
			dataset (tsv file) : AA aggregated results file
			oncogene_list (list) : parsed list of oncogenes
		Return: 
			None
		"""
		# 	TODO
		# 	if self.loc_type = sample:
		# 		collapse dataset by sample
		if self.loc_type != "":
			sample_datasubset = dataset[dataset['Classification'] == self.amp_type]
	
		id = 0
		for index, row in sample_datasubset.iterrows():
			genelist = self.ExtractGenes(str(row['All genes']))
			for gene in genelist:
				if gene == '':
					continue
				current_sample = row['Feature ID']
				found_node = False
				for node in self.nodelist:
					if node.GetLabel() == gene:
						node.AddLoc(current_sample)
						found_node = True
						break
				if found_node == False:
					id += 1
					oncogene = gene in oncogene_list
					node = Node(id, gene, oncogene, [current_sample])
					self.nodelist.append(node)

		for node1 in self.nodelist:
			i = self.nodelist.index(node1) + 1
			for j in range(i, len(self.nodelist)):
				intersect_ij = node1.Intersect(self.nodelist[j])
				union_ij = node1.Union(self.nodelist[j])
				edge_weight = len(intersect_ij)/len(union_ij)
				if edge_weight > self.threshold:
					if node1 not in self.graph:
						self.graph[node1] = []
					if self.nodelist[j] not in self.graph:
						self.graph[self.nodelist[j]] = []
					self.graph[node1].append((node1, self.nodelist[j], edge_weight, "in"))
					self.graph[self.nodelist[j]].append((self.nodelist[j], node1, edge_weight, "out"))
					self.number_edges += 1
		
	def NumNodes(self): # Michael
		"""
		Get the number of genes in the graph
	
		Parameters: 
			self (Graph) : Graph object
		Return: 
			int: number of nodes in graph object
		"""
		return len(self.nodelist)

	def Nodes(self): # Dhruv
		"""
		Get all nodes (genes) in graph
	
		Parameters: 
				self (Graph) : Graph object
		Return: 
				list[str]: nodes (genes) in graph object
		"""
		return self.nodelist

	def NumEdges(self): # Dhruv
		"""
		Get the number of edges in the graph

		Parameters: 
			self (Graph) : Graph object 
		Return: 
			int : number of edges in graph object
		"""
		return self.number_edges

	def EdgeWeight(self, u, v): # Dhruv
		"""
		Get the weight of the edge between u and v
		Parameters: 
			self (Graph) : Graph object
			u (Node) : Node belonging to gene1
			v (Node) : Node belonging to gene2
		Return: 
			int: Weight of edge connecting node u and node v
		"""
		outgoing_edges = self.graph[u]
		for edge in outgoing_edges:
			if edge[1] == v:
				return edge[2]

	def NumNeighbors(self, u): # Dhruv
		"""
		Get the number of neighbors of a given node u in the graph
	
		Parameters: 
			self (Graph) : Graph object
			u (Node) : Node belonging to gene1
		Return: 
			int : number of neighbors of node u in graph object
		"""
		return len(self.graph[u])

	def Neighbors(self, u): # Michael
		"""
		Get the neighbors of a given node u in the graph
	
		Parameters: 
			self (Graph) : Graph object
			u (Node) : Node belonging to gene1
		Return: 
			list[str] : list of neighbors of node u in graph object
		"""
		neighbors = list()
		for x in self.graph.get(u):
			neighbors.append(x[0])
		return neighbors
	
	def Explore(self, node, visited, currCycle):
		"""
		Traverse all reachable nodes from start, append to currCycle
	
		Parameters: 
			self (Graph) : Graph object
			node (str) : start node (represents a gene)
			visited (dict[str : bool]) : visited status of each node in graph
			currCycle (list[str]) : list of nodes in the current cycle
		Return: 
			list[str] : list representing the current connected component (gene labels)
		"""
		if node not in self.nodelist:
			return
		visited[node] = True
		currCycle.append(node)
		#print(self.graph.get(node))
		for endNode in self.graph.get(node):
			if not visited[endNode[1]]:
				self.Explore(endNode[1], visited, currCycle)
		return currCycle

	def CC(self): # Kyra
		"""
		Get the connected components of the graph object
	
		Parameters: 
			self (Graph) : Graph object
		Return: 
			list[list[str]] : list of each connected component (gene labels)
		"""
		cycles = list()
		visited = dict()
		for node in self.nodelist:
			visited[node] = False
		for node in self.nodelist:
			if not visited[node]:
				currCycle = list()
				currCycle = self.Explore(node, visited, currCycle)
				cycles.append(currCycle)
		return cycles
		
	def Export(self, outfile="graph.tsv", nodefile=None): # Michael
		"""
		Export the graph in a table representation compatible with Cytoscape	
		
		Parameters: 
			self (Graph) : Graph object
		Return: 
			tsv file : graph represented as edge list with edge = [u, v, weight, in/out]	
		"""
		# convert adjacency list to edge list
		edgelist = list()
		for start, ends in self.graph.items():
			for end in ends:
				if end[3] == "in":
					# edgelist.append((start.GetLabel(), end[1].GetLabel(), end[2], len(start.Union(end[1]))))
					# format sample list
					union = [s.split("_")[0] for s in start.Union(end[1])]
					edgelist.append((start.GetID(), end[1].GetID(), end[2], len(union), '|'.join(union)))
		# export edge list
		with open(outfile, 'wt') as f:
			writer = csv.writer(f) #, delimiter='\t')
			writer.writerow(['source', 'target', 'weight', 'lenunion', 'union'])
			for edge in edgelist:
				writer.writerow([edge[0], edge[1], edge[2], edge[3], edge[4]])
		# export node list (for oncogene status)
		if nodefile is not None:
			with open(nodefile, 'wt') as f:
				writer = csv.writer(f) #, delimiter='\t')
				writer.writerow(['id', 'label', 'oncogene_status'])
				for node in self.nodelist:
					writer.writerow([node.GetID(), node.GetLabel(), node.GetOncogeneStatus()])				
	
	def Read(self, table): # Dhruv
		"""
		Read in a pre-constructed graph of format specified by Export()
	
		Parameters: 
			self (Graph) : Graph object
			table (tsv file) : graph represented as edge list
		Return: 
			Graph : Graph object representative of the graph specified by table
		"""
		# Return graph
		read_table = pd.read_csv(table, sep = '\t')

		added_genes = {}

		for index, row in read_table.iterrows():
			gene1 = row[0]
			gene2 = row[1]
			if gene1 not in added_genes:
				node1 = Node(gene1, [])
				added_genes[gene1] = node1
				self.nodelist.append(node1)
			if gene2 not in added_genes:
				node2 = Node(gene2, [])
				added_genes[gene2] = node2
				self.nodelist.append(node2)
			edgeweight = row[2]
			if added_genes[gene1] not in self.graph:
				self.graph[added_genes[gene1]] = []
			current_edge = (added_genes[gene1], added_genes[gene2], edgeweight, "in")
			if current_edge not in self.graph[added_genes[gene1]]:
				self.graph[added_genes[gene1]].append(current_edge)
			if added_genes[gene2] not in self.graph:
				self.graph[added_genes[gene2]] = []
			current_edge = (added_genes[gene2], added_genes[gene1], edgeweight, "out")
			if current_edge not in self.graph[added_genes[gene2]]:
				self.graph[added_genes[gene2]].append(current_edge)
			self.number_edges += 1

	def Subgraph(self, gene_list, threshold=0): # Michael
		"""
		Get an induced subgraph S of the graph object. An edge between nodes u 
		and v is considered part of S only if u and v both appear in gene_list
	
		Parameters: 
			self (Graph) : Graph object
			gene_list (list[str]) : list of genes
		Return: 
			Graph : graph object representative of the induced subgraph
		"""
		subgraph = Graph()
		labels = []
		for node in self.nodelist:
			if node.GetLabel() in gene_list:
				subgraph.nodelist.append(node)
				labels.append(node.GetLabel())
		for node in subgraph.nodelist:
			for edge in self.graph.get(node):
				if edge[1].GetLabel() in labels and edge[2] > max(threshold, self.threshold):
					if node not in subgraph.graph:
						subgraph.graph[node] = []
					subgraph.graph[node].append(edge)
		return subgraph
	
	def Print(self, input=None, threshold=0): # Michael
		"""
		Print graph in readable format for debugging

		Parameters:
			input (Graph) : other graph to read in (can also make input (dict))
		Return: 
			"[start] : ([end], [weight]), ([end, weight])"
		"""
		graph = self.graph if input is None else input.graph
		for start, ends in graph.items():
			print(start.GetLabel(), " (Oncogene ", start.GetOncogeneStatus(), "): ", sep="", end="")
			for end in ends:
				if end[2] > max(threshold, self.threshold):
					print("({node},{weight:.2f},{dir})".format(node = end[1].GetLabel(), weight = end[2], dir = end[3]), end=" ")
			print()
