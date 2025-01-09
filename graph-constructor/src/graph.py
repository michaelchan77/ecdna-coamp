import re
import pandas as pd
import numpy as np
from collections import defaultdict

# attempt to streamline by creating node and edge dataframes directly
class Graph:

	def __init__(self, dataset=None, aliasdict=None, amp_type="ecDNA", loc_type="amplicon"):
		"""
		Parameters:
			self (Graph) : Graph object 
			dataset (tsv file) : AA aggregated results file
			amp_type (str) : type of focal amplification (ecDNA, BFB, etc.)
			loc_type (str) : cell line or amplicon feature
		Return:
			None
		"""
		if dataset is None:
			print("Error: provide Amplicon Architect annotations")	
		if aliasdict is None:
			print("Error: provide dictionary of DepMap names")	
		else:
			self.amp_type = amp_type
			self.loc_type = loc_type
			self.nodes_df = pd.DataFrame({
				"label": [],								# str
				"alias": [],								# str
				"oncogene_status": pd.Series(dtype=bool),	# bool
				"amplicons": pd.Series(dtype=object)		# list
				# "cell_lines": pd.Series(dtype=object)		# list	
				# "tissues": pd.Series(dtype=object)		# list
			})
			# self.edges_df = pd.DataFrame({
			# 	"source": [],  								# int
			# 	"target": [],								# int
			# 	"weight": [],								# float
			# 	"inter": pd.Series(dtype=object),			# list
			# 	"union": pd.Series(dtype=object)			# list
			# })
			self.CreateNodes(dataset, aliasdict)
			self.CreateEdges()

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

	def CreateNodes(self, dataset, aliasdict):
		"""
		Create a nodes_df by iterating through the dataset, adding new genes to 
		a list of dictionaries. Update the amplicons for existing genes, then 
		merge the list into the dataframe after processing.
				
		Parameters: 
			self (Graph) : Graph object 
			dataset (tsv file) : AA aggregated results file
			aliasdict (df) : mapping of RefGene to DepMap gene names
		Return: 
			None
		"""
		TEST_NAMES_NOT_MAPPED_COUNT = 0
		# dictionary for fast lookups of gene labels
		gene_index = {}
		# list to store new rows for concatenation
		new_genes = []

		# get subset of ecDNA amplicons
		if self.loc_type == "amplicon":
			amplicons = dataset[dataset['Classification'] == self.amp_type]
		# for each amplicon
		for __, row in amplicons.iterrows():
			# get the genes in this amplicon
			oncogenes = set(self.ExtractGenes(str(row['Oncogenes'])))
			allgenes = self.ExtractGenes(str(row['All genes']))
			for gene in allgenes:
				currentamp = row['Feature ID']
				# if the gene has been seen, add this amplicon to its list
				if gene in gene_index:
					index = gene_index[gene]
					new_genes[index]['amplicons'].append(currentamp)
				# otherwise add the gene to new_genes as a new row
				else:
					alias = aliasdict.get(gene)
					if alias is None:
						TEST_NAMES_NOT_MAPPED_COUNT += 1
					new_gene = {
						'label': gene,
						'alias': '' if alias is None else alias,
						'oncogene_status': gene in oncogenes,
						'amplicons': [currentamp]
                	}
					new_genes.append(new_gene)
					gene_index[gene] = len(new_genes) - 1
		# concatenate all new genes as rows
		if new_genes:
			new_gene_df = pd.DataFrame(new_genes)
			self.nodes_df = pd.concat([self.nodes_df, new_gene_df], ignore_index=True)

		print('No alias found for', TEST_NAMES_NOT_MAPPED_COUNT, 'genes.')
			
	def CreateEdges(self):
		"""
		Create edges by iterating through pairs of nodes in nodes_df based on 
		shared amplicons. Calculate edge properties for each pair, and append 
		the results to the edges_df after processing all pairs.
				
		Parameters: 
			self (Graph) : Graph object 
		Return: 
			None
		"""
		self.nodes_df = self.nodes_df.reset_index(drop=True)

		# extract relevant columns
		labels = self.nodes_df['label'].values
		amplicons = self.nodes_df['amplicons'].values
		
		# build reverse index to map amplicons to nodes
		amplicon_to_nodes = defaultdict(list)
		for index, amps in enumerate(amplicons):
			for amp in amps:
				amplicon_to_nodes[amp].append(index)

		# collect potential node pairs, avoiding duplicates
		potential_pairs = set()
		for nodelist in amplicon_to_nodes.values():
			for i, node1 in enumerate(nodelist):
				for node2 in nodelist[i + 1:]:
					potential_pairs.add((node1, node2)) 

		# unzip pairs into source and target nodes
		pairs = list(potential_pairs)
		src_indices, tgt_indices = zip(*pairs)
		
		# retrieve the matching amplicons for all source and target nodes
		src_amplicons = [amplicons[i] for i in src_indices]
		tgt_amplicons = [amplicons[j] for j in tgt_indices]
		
		# calculate all intersections and unions
		inters = [list(set(s) & set(t)) for s,t in zip(src_amplicons, tgt_amplicons)]
		unions = [list(set(s) | set(t)) for s,t in zip(src_amplicons, tgt_amplicons)]

		# filter pairs with non-empty intersections
		non_empty_mask = [len(inter) > 0 for inter in inters]
		src_filtered = [src_indices[i] for i, mask in enumerate(non_empty_mask) if mask]
		tgt_filtered = [tgt_indices[i] for i, mask in enumerate(non_empty_mask) if mask]
		inters_filtered = [inters[i] for i, mask in enumerate(non_empty_mask) if mask]
		unions_filtered = [unions[i] for i, mask in enumerate(non_empty_mask) if mask]

		# calculate weights
		weights = [len(i) / len(u) for i,u in zip(inters_filtered, unions_filtered)]

		# create edges dataframe
		self.edges_df = pd.DataFrame({
			'source': [labels[i] for i in src_filtered],
			'target': [labels[j] for j in tgt_filtered],
			'weight': weights,
			'inter': inters_filtered,
			'union': unions_filtered
		})

	# get functions
	# -------------
	def NumNodes(self):
		try:
			return len(self.nodes_df)
		except:
			print('Error: build graph')

	def NumEdges(self):
		try:
			return len(self.edges_df)
		except:
				print('Error: build graph')
	
	def Nodes(self):
		try:
			return self.nodes_df
		except:
			print('Error: build graph')

	def Edges(self):
		try:
			return self.edges_df
		except:
			print('Error: build graph')
	
	"""
	# PREV CREATE_NODES SNIPPET
	# add this amplicon to the gene's list of amplicons
	row_matched = self.nodes_df[self.nodes_df['label'] == gene]
	if not row_matched.empty:
		index = row_matched.index[0]
		self.nodes_df.at[index, 'amplicons'].append(currentamp)
	# or add the gene to nodes_df if not present
	else:
		new_gene = pd.DataFrame({
			'label': gene, 
			'alias': gene, 
			'oncogene_status': gene in oncogenes, 
			'amplicons': [[currentamp]] 
		})
		self.nodes_df = pd.concat([self.nodes_df, new_gene], ignore_index=True)
	"""