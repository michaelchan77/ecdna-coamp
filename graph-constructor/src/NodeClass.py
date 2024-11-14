class Node:

	def __init__(self, ident, label, oncogene, alias, locs=list()): # Kyra
		"""
		Parameters:
			self (Node) : Node object 
			label (str) : gene name
			locs (list[str]) : list of features or samples where gene appears
			oncogene (bool) : oncogene status
		Return:
			None
		"""
		self.id = ident
		self.label = label
		self.oncogene = oncogene
		self.locs = locs
		self.alias = alias
	
	def GetAlias(self):
		"""
		Parameters: 
			self (Node) : Node object 
		Return: 
			alias : gene alias
		"""
		return '' # temp
		return self.alias

	def GetID(self):
		"""
		Parameters: 
			self (Node) : Node object 
		Return: 
			id : gene id
		"""
		return self.id

	def GetLabel(self): # Kyra
		"""
		Parameters: 
			self (Node) : Node object 
		Return: 
			str : gene name
		"""
		return self.label
	
	def GetOncogeneStatus(self):
		"""
		Parameters: 
			self (Node) : Node object 
		Return: 
			bool : oncogene status
		"""
		return self.oncogene

	def GetLocs(self): # Kyra
		"""
		Parameters:
			self (Node): Node object
		Return:
			list[str] : list of features or samples where gene appears
		"""
		return self.locs

	def AddLoc(self, loc): # Michael
		"""
		Add a sample or feature to the list of locations where gene appears on

		Parameters: 
			self (Node) : Node object
			loc (str) : name of sample or feature that gene belongs to
		Return: 
			None
		"""
		self.locs.append(loc)
	
	def Intersect(self, v): # Kyra 
		"""
		Get list of locations shared by genes in nodes self and v

		Parameters:
			self (Node): Node object
			v (Node) : Node object
		Return:
			list[str] : intersection of the locs lists of node1 and node2
		"""
		v_locs = set(v.locs)
		intersection = [loc for loc in self.locs if loc in v_locs]
		return intersection

	def Union(self, v): # Kyra
		"""
		Get list of locations where either gene in nodes self or v appear
		Parameters: 
			self (Node): Node object
			v (Node) : Node belonging
		Return: 
			list[str]: samples in common between two genes provided
		"""
		return list(set(self.locs + v.locs))