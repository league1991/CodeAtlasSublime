# -*- coding: utf-8 -*-

class SymbolAttr(object):
	ATTR_UI      	 = 0
	ATTR_REF		 = 1
	ATTR_NUM		 = 2
	def __init__(self):
		self.node = None

class UIAttr(SymbolAttr):
	def __init__(self, depth=0, nLeaf=0):
		self.subtreeDepth = depth
		self.subtreeNLeaf = nLeaf
		self.subtreeNPinnedLeaf = 0
		self.baseRadius = 0
		self.minR = 0
		self.maxR = 0
		self.minTheta = 0
		self.maxTheta = 0
		self.uiItem = None
		self.isPinned = False
		self.isAncestorPinned = False
		self.isIgnored = False

	def setPinned(self, pinned):
		self.isPinned = pinned

	def setIgnored(self, ignored):
		self.isIgnored = ignored

	def setUIItem(self, item):
		self.uiItem = item

	def getUIItem(self):
		return self.uiItem

class RefAttr(SymbolAttr):
	def __init__(self, nCall = 0, nCalled = 0):
		self.nCall = nCall
		self.nCalled = nCalled

	def getCallerCalleeDiff(self):
		return self.nCall - self.nCalled

attrDict = {SymbolAttr.ATTR_UI : UIAttr, SymbolAttr.ATTR_REF: RefAttr}
def createAttr(attrType):
	klass = attrDict.get(attrType)
	if not klass:
		return None
	return klass()