# -*- coding: utf-8 -*-
import time
import sys
from PyQt4 import QtCore, QtGui, uic, Qt
import math
import random
from db.SymbolAttr import UIAttr, RefAttr
from ui.SymbolUIItem import SymbolUIItem

class RefData(object):
	REF_CALL = 0
	def __init__(self, type):
		self.type = type

class LineCache(object):
	N_POINTS = 14
	COLOR_TABLE = []
	SRC_COLOR = QtGui.QColor(237,6,6)
	MID_COLOR = QtGui.QColor(200,200,200)
	DST_COLOR = QtGui.QColor(0,209,192)
	def __init__(self, start, end):
		self.startPnt = start
		self.endPnt = end
		self.path = QtGui.QPainterPath()
		self.path.moveTo(self.startPnt)
		self.path.cubicTo(self.startPnt* 0.5,
						  self.endPnt*0.5,
						  self.endPnt)

		self.isVisible = True
		self.weight = 1
		# nPnts = LineCache.N_POINTS
		# self.pntList = [None] * nPnts
		# for i in range(nPnts):
		# 	t = i / float(nPnts-1)
		# 	self.pntList[i] = QtCore.QPointF(self.path.pointAtPercent(t))
		#
		# if not self.COLOR_TABLE:
		# 	srcClr = (93,195,187)
		# 	tarClr = (255,104,104)
		# 	for i in range(nPnts-1):
		# 		t = i / float(nPnts-2)
		# 		c = [0,0,0]
		# 		for j in range(3):
		# 			c[j] = srcClr[j] * (1-t) + tarClr[j] * t
		# 		self.COLOR_TABLE.append(QtGui.QColor(c[0],c[1],c[2],50))

	def setVisible(self, visible):
		self.isVisible = visible

	def paint(self, qPainter, alpha = 50, width = 1):
		if not self.isVisible:
			return
		gradient = QtGui.QLinearGradient(self.startPnt, self.endPnt)
		self.SRC_COLOR.setAlpha(alpha)
		self.MID_COLOR.setAlpha(alpha)
		self.DST_COLOR.setAlpha(alpha)
		gradient.setColorAt(0.0, self.SRC_COLOR)
		gradient.setColorAt(0.5, self.MID_COLOR)
		gradient.setColorAt(1.0, self.DST_COLOR)
		qPainter.setPen(QtGui.QPen(QtGui.QBrush(gradient), width))

		#for i in range(LineCache.N_POINTS-1):
		#	qPainter.setPen(self.COLOR_TABLE[i])
		#	qPainter.drawLine(self.pntList[i], self.pntList[i+1])
		qPainter.drawPath(self.path)
		#qPainter.drawLine(self.startPnt, self.endPnt)

class SymbolScene(QtGui.QGraphicsScene):
	def __init__(self, *args):
		super(SymbolScene, self).__init__(*args)
		self.symbolRoot = None
		self.symbolDict = {}
		self.baseRadius = 200
		self.totalRadius = 20
		self.unpinnedAngle = 1
		self.pinnedAngle   = 1

		self.highPosList   = []
		self.normalPosList = []
		self.lowPosList    = []

		self.callRef = {}

		from db.SymbolNode import SymbolNode
		self.widthDict = {SymbolNode.KIND_NAMESPACE: 10,
						  SymbolNode.KIND_FUNCTION:  30,
						  SymbolNode.KIND_VARIABLE:  10,
						  SymbolNode.KIND_CLASS:	 10,
						  SymbolNode.KIND_UNKNOWN:   10}

		self.setItemIndexMethod(QtGui.QGraphicsScene.BspTreeIndex)

	def getBaseRadius(self):
		return self.baseRadius

	def buildScene(self):
		from db.DBManager import DBManager
		dbObj = DBManager.instance().getDB()

		self.callRef = {}

		self.symbolRoot, self.symbolDict = dbObj.buildSymbolTree()
		if not self.symbolRoot or not self.symbolDict:
			return
		self._buildRef()
		self._buildUI()

	def refreshUI(self):
		self._buildUI()

	def _buildUI(self):
		if self.symbolRoot is None:
			return
		self._buildRefAttr()
		depth, nLeaf, nPinnedLeaf, maxR = self._layoutButtonUp(self.symbolRoot)
		rootAttr = self.symbolRoot.getAttr(UIAttr.ATTR_UI)
		rootAttr.maxR = rootAttr.minR + 1
		self.totalRadius = rootAttr.maxR

		idealPinnedAngle = 5.0
		pinnedScore = 1.0 * nPinnedLeaf
		unpinnedScore = (360.0 / idealPinnedAngle - 1) / (nLeaf-1) * (nLeaf - nPinnedLeaf)
		if nPinnedLeaf > 0:
			self.pinnedAngle = math.pi * 2.0 * pinnedScore / (pinnedScore+unpinnedScore) / nPinnedLeaf
		if nLeaf - nPinnedLeaf > 0:
			self.unpinnedAngle = math.pi * 2.0 * unpinnedScore / (pinnedScore+unpinnedScore) / (nLeaf-nPinnedLeaf)

		self._layoutTopDown(self.symbolRoot, 0, math.pi * 2.0, False)
		self._buildLines()

	def getHighPosList(self):
		return self.highPosList

	def getNormalPosList(self):
		return self.normalPosList

	def getLowPosList(self):
		return self.lowPosList

	def _buildLines(self):
		from db.SymbolAttr import SymbolAttr
		scene = self
		refDict = scene.getCallDict()
		self.highPosList   = []
		self.normalPosList = []
		self.lowPosList    = []

		classCallDict = {}
		for key, ref in refDict.items():
			callerNode = scene.getNode(key[0])
			calleeNode = scene.getNode(key[1])
			if not callerNode or not calleeNode:
				continue
			callerAttr = callerNode.getAttr(SymbolAttr.ATTR_UI)
			calleeAttr = calleeNode.getAttr(SymbolAttr.ATTR_UI)
			callerItem = callerAttr.getUIItem()
			calleeItem = calleeAttr.getUIItem()
			callerPnt = callerItem.getCurveSlot()
			calleePnt = calleeItem.getCurveSlot()

			# hide member functions when unpinned
			visible = True
			if callerNode.parent == calleeNode.parent and callerNode.parent and callerNode.parent.getKind() == callerNode.KIND_CLASS:
				parentAttr = callerNode.parent.getAttr(UIAttr.ATTR_UI)
				if parentAttr and parentAttr.isPinned == False:
					continue

			line = LineCache(QtCore.QPointF(callerPnt[0], callerPnt[1]),
							 QtCore.QPointF(calleePnt[0], calleePnt[1]))

			if callerAttr.isAncestorPinned or calleeAttr.isAncestorPinned or callerAttr.isPinned or calleeAttr.isPinned:
				self.highPosList.append(line)
			elif callerNode.parent and calleeNode.parent and\
					callerNode.parent.getKind() == callerNode.KIND_CLASS and calleeNode.parent.getKind() == calleeNode.KIND_CLASS:
				key = (callerNode.parent.uniqueName, calleeNode.parent.uniqueName)
				callLine = classCallDict.get(key)
				if not callLine:
					callerAttr = callerNode.parent.getAttr(SymbolAttr.ATTR_UI)
					calleeAttr = calleeNode.parent.getAttr(SymbolAttr.ATTR_UI)
					callerItem = callerAttr.getUIItem()
					calleeItem = calleeAttr.getUIItem()
					callerPnt  = callerItem.getCurveSlot()
					calleePnt  = calleeItem.getCurveSlot()
					line = LineCache(	QtCore.QPointF(callerPnt[0], callerPnt[1]),
							 			QtCore.QPointF(calleePnt[0], calleePnt[1]))
					classCallDict[key] = line
					line.weight = 1
				else:
					classCallDict[key].weight += 1
			else:
			# elif callerAttr.isIgnored or calleeAttr.isIgnored:
			# 	self.lowPosList.append(line)
			# else:
			 	self.normalPosList.append(line)

		self.normalPosList.extend(classCallDict.values())

	def _buildRefAttr(self):
		for uname, node in self.symbolDict.items():
			refAttr = node.getOrAddAttr(RefAttr.ATTR_REF)
			refAttr.nCall = 0
			refAttr.nCalled = 0

		for srcName, tarName in self.callRef:
			srcNode = self.symbolDict.get(srcName)
			tarNode = self.symbolDict.get(tarName)
			if not srcNode or not tarNode:
				continue

			srcRef = srcNode.getAttr(RefAttr.ATTR_REF)
			tarRef = tarNode.getAttr(RefAttr.ATTR_REF)
			srcRef.nCall   +=1
			tarRef.nCalled +=1

	def _layoutButtonUp(self, node):
		depth = 0
		nLeaf = 0
		nPinnedLeaf = 0
		minR  = 0
		for uname, child in node.getChildDict().items():
			childDepth, leafCount, pinnedLeafCount, childR  = self._layoutButtonUp(child)
			depth = max(depth, childDepth)
			nLeaf += leafCount
			nPinnedLeaf += pinnedLeafCount
			minR  = max(minR, childR)

		if len(node.getChildDict()) == 0:
			nLeaf = 1
			minR = self.baseRadius
		depth += 1

		layoutAttr = node.getOrAddAttr(UIAttr.ATTR_UI)
		if layoutAttr.isPinned:
			nPinnedLeaf = nLeaf

		layoutAttr.subtreeDepth = depth
		layoutAttr.subtreeNLeaf = nLeaf
		layoutAttr.subtreeNPinnedLeaf = nPinnedLeaf
		layoutAttr.minR = minR

		maxR = minR + self.widthDict[node.getKind()]
		return depth, nLeaf, nPinnedLeaf, maxR

	def _layoutTopDown(self, node, minTheta, maxTheta, isPinned):
		nodeAttr = node.getAttr(UIAttr.ATTR_UI)
		nodeAttr.minTheta = minTheta
		nodeAttr.maxTheta = maxTheta
		nodeAttr.isAncestorPinned = isPinned

		uiItem = nodeAttr.uiItem
		if not uiItem:
			uiItem = SymbolUIItem(node)
			nodeAttr.uiItem = uiItem
			uiItem.buildUI(nodeAttr, self)
			self.addItem(uiItem)
		else:
			uiItem.buildUI(nodeAttr, self)

		# dTheta = float(maxTheta - minTheta) / nodeAttr.subtreeNLeaf
		begTheta = minTheta
		childList = list(node.getChildDict().values())
		childList.sort(key=lambda x:(x.defineFile, x.kind, x.getAttr(RefAttr.ATTR_REF).getCallerCalleeDiff()))
		#print('-----------------------------------------------------')
		for child in childList:
			#print(child.defineFile)
			childAttr = child.getAttr(UIAttr.ATTR_UI)
			childAttr.maxR = nodeAttr.minR
			newBegTheta = begTheta
			pinned = isPinned or childAttr.isPinned
			if pinned:
				newBegTheta += childAttr.subtreeNLeaf * self.pinnedAngle
			else:
				newBegTheta += childAttr.subtreeNPinnedLeaf * self.pinnedAngle + (childAttr.subtreeNLeaf - childAttr.subtreeNPinnedLeaf) * self.unpinnedAngle

			self._layoutTopDown(child, begTheta, newBegTheta, pinned)
			begTheta = newBegTheta

	def _buildRef(self):
		from db.DBManager import DBManager
		dbObj = DBManager.instance().getDB()

		for uname, symbol in self.symbolDict.items():
			unameList, refList = dbObj.searchRefEntity(uname, 'call', '*', True)
			for tarUname in unameList:
				self.callRef[(uname, tarUname)] = RefData(RefData.REF_CALL)

	def pinSymbol(self, isPinned):
		itemList = self.selectedItems()
		if not itemList:
			return

		from db.SymbolAttr import SymbolAttr
		for item in itemList:
			node = item.getNode()
			attr = node.getOrAddAttr(SymbolAttr.ATTR_UI)
			attr.setPinned(isPinned)

		self.refreshUI()

	def ignoreSymbol(self, isIgnored):
		itemList = self.selectedItems()
		if not itemList:
			return

		from db.SymbolAttr import SymbolAttr
		for item in itemList:
			node = item.getNode()
			attr = node.getOrAddAttr(SymbolAttr.ATTR_UI)
			attr.setIgnored(isIgnored)

		self.refreshUI()

	def getCallDict(self):
		return self.callRef

	def getNode(self, uniqueName):
		return self.symbolDict.get(uniqueName, None)

	def updateNodeVisibility(self, lod):
		t0 = time.clock()
		# for uname, node in self.symbolDict.items():
		# 	attr = node.getAttr(UIAttr.ATTR_UI)
		# 	if not attr:
		# 		continue
		# 	item = attr.getUIItem()
		# 	if not item:
		# 		continue
			#al = item.getMaxArcLength() * lod
			#item.setVisible(al > 5)

		r = self.baseRadius * lod
		for item in self.items():
			al = r * (item.theta[1] - item.theta[0])
			item.setVisible(al > 2)

		t1 = time.clock()
		#print("time is ", (t1-t0))
