# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtCore, QtGui, uic
import math
import random

import traceback
import threading
import time

class SceneUpdateThread(threading.Thread):
	def __init__(self, scene, lock):
		threading.Thread.__init__(self)
		self.scene = scene
		self.lock = lock
		self.isActive = True

		self.itemSet = set()

	def setActive(self, isActive):
		self.lock.acquire()
		self.isActive = isActive
		self.lock.release()

	def run(self):
		while True:
			if self.isActive:
				self.lock.acquire()
				#self.updatePos()
				if self.itemSet != set(self.scene.itemDict.keys()):
					self.updateLayeredLayout()
				self.moveItems()
				self.lock.release()

				self.scene.invalidate()

			time.sleep(0.05)

	def updatePos(self):
		import ui.CodeUIItem as CodeUIItem
		posList = [item.pos() for item in self.scene.itemDict.values()]
		rList = [item.getRadius() for item in self.scene.itemDict.values()]
		kindList = [item.getKind() for item in self.scene.itemDict.values()]
		isSourceItem = [True] * len(posList)

		posDict = {}
		i = 0
		for itemName, item in self.scene.itemDict.items():
			posDict[itemName] = i
			i+= 1

		nPos = len(posList)
		for i in range(nPos):
			posI = posList[i]
			rI = rList[i]
			for j in range(nPos):
				if i == j:
					continue
				posJ = posList[j]
				dp = posI - posJ
				dpLengthSq = dp.x()*dp.x() + dp.y()*dp.y()
				dpLength = math.sqrt(dpLengthSq)

				if dpLengthSq < 1e-3:
					continue

				force = max(1.0 / (dpLength+1.0) * 10 * math.sqrt(rI * rList[j]) - 1, 0)
				offset = dp * (1.0 / dpLength * min(force,1))
				posList[i] += offset
				posList[j] -= offset

		for edgeName in self.scene.edgeDict.keys():
			i = posDict[edgeName[0]]
			j = posDict[edgeName[1]]
			isSourceItem[j] = False
			posI = posList[i]
			posJ = posList[j]
			dp = posI - posJ
			dpLengthSq = dp.x()*dp.x() + dp.y()*dp.y()
			dpLength = math.sqrt(dpLengthSq)
			if dpLength < 1e-3:
				continue

			force = dpLengthSq * 0.01
			offset = dp * (1.0 / dpLength * min(force,1))
			# if kindList[i] == CodeUIItem.ITEM_FUNCTION and kindList[j] == CodeUIItem.ITEM_VARIABLE:
			# 	posList[j] = posJ + offset
			# elif kindList[j] == CodeUIItem.ITEM_FUNCTION and kindList[i] == CodeUIItem.ITEM_VARIABLE:
			# 	posList[i] = posJ + offset
			# else:
			posList[i] = posI - offset
			posList[j] = posJ + offset

		# for i in range(nPos):
		# 	if kindList[i] == CodeUIItem.ITEM_FUNCTION and not isSourceItem[i]:
		# 		posList[i] = posList[i] + QtCore.QPointF(1,0)

		# i=0
		# for itemName, item in self.scene.itemDict.items():
		# 	#if not isSourceItem[i]:
		# 	item.setPos(posList[i])
		# 	#print(posList[i])
		# 	i += 1

		i=0
		for itemName, item in self.scene.itemDict.items():
			item.setTargetPos(posList[i])
			i+=1

	def updateLayeredLayout(self):
		#print('update layered layout')
		from grandalf.graphs import Vertex, Edge, Graph

		class VtxView(object):
			def __init__(self, w, h):
				self.w = w
				self.h = h

		self.itemSet = set()
		V = []
		vid = {}
		for name, item in self.scene.itemDict.items():
			r = item.getRadius()
			vtx = Vertex(item.getUniqueName())
			vtx.view = VtxView(r*2.0, r*2.0)
			vid[name] = len(V)
			V.append(vtx)
			self.itemSet.add(name)

		E = []
		for edgeKey, edge in self.scene.edgeDict.items():
			vi = vid.get(edgeKey[0], None)
			vj = vid.get(edgeKey[1], None)
			if vi is None or vj is None:
				continue
			E.append(Edge(V[vi], V[vj]))

		g = Graph(V,E)
		if len(g.C) <= 0:
			return

		from grandalf.layouts import SugiyamaLayout
		sug = SugiyamaLayout(g.C[0])
		sug.init_all()
		sug.draw(5)

		for v in g.C[0].sV:
			item = self.scene.itemDict.get(v.data)
			if item:
				item.setTargetPos(QtCore.QPointF(v.view.xy[1], v.view.xy[0]))

	def moveItems(self):
		for name, item in self.scene.itemDict.items():
			item.moveToTarget(0.05)

class CodeScene(QtGui.QGraphicsScene):
	def __init__(self, *args):
		super(CodeScene, self).__init__(*args)
		self.itemDict = {}
		self.edgeDict = {}
		self.itemLruQueue = []
		self.lruMaxLength = 50

		self.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
		self.lock = threading.RLock()
		self.updateThread = SceneUpdateThread(self, self.lock)
		self.updateThread.start()

		self.connect(self, QtCore.SIGNAL('selectionChanged()'), self, QtCore.SLOT('onSelectItems()'))

	def setAlphaFromLru(self):
		ithItem = 0
		for itemKey in self.itemLruQueue:
			item = self.itemDict.get(itemKey, None)
			# if item:
			# 	item.setOpacity(1.0 - float(ithItem) / self.lruMaxLength)
			ithItem += 1

	def deleteLRU(self, itemKeyList):
		for itemKey in itemKeyList:
			if itemKey in self.itemLruQueue:
				self.itemLruQueue.remove(itemKey)

	def updateLRU(self, itemKeyList):
		deleteKeyList = []
		for itemKey in itemKeyList:
			idx = None
			for i in range(len(self.itemLruQueue)):
				if itemKey == self.itemLruQueue[i]:
					idx = i

			if idx is None:
				queueLength = len(self.itemLruQueue)
				if queueLength > self.lruMaxLength:
					pass
					# lastIdx = len(self.itemLruQueue)-1
					# deleteKeyList.append(self.itemLruQueue[lastIdx])
					# del self.itemLruQueue[lastIdx]
			else:
				# 已有的项
				del self.itemLruQueue[idx]

			self.itemLruQueue.insert(0, itemKey)
		print('------------- update lru -------------')
		for i, key in enumerate(self.itemLruQueue):
			print(i, self.itemDict[key].name)
		print('--------------------------------------')
		return []#deleteKeyList

	def removeItemLRU(self):
		queueLength = len(self.itemLruQueue)
		#print ('remove item lru', queueLength, self.lruMaxLength)

		if queueLength > self.lruMaxLength:
			for i in range(self.lruMaxLength, queueLength):
				self._doDeleteCodeItem(self.itemLruQueue[i])

			self.itemLruQueue = self.itemLruQueue[0:self.lruMaxLength]

		for idx, itemName in enumerate(self.itemLruQueue):
			item = self.itemDict.get(itemName, None)
			# if item:
			# 	opacity = 1.0 - float(idx) / self.lruMaxLength
			# 	item.setOpacity(opacity)
				#print(idx, item, opacity)

	def acquireLock(self):
		self.lock.acquire()

	def releaseLock(self):
		self.lock.release()

	def _doAddCodeItem(self, uniqueName):
		item = self.itemDict.get(uniqueName, None)
		if item:
			return False, item
		from ui.CodeUIItem import CodeUIItem
		item = CodeUIItem(uniqueName)
		item.setPos(random.uniform(-1,1), random.uniform(-1,1))
		self.itemDict[uniqueName] = item
		self.addItem(item)
		return True, item

	def addCodeItem(self, uniqueName):
		self.lock.acquire()
		res, item = self._doAddCodeItem(uniqueName)
		self.updateLRU([uniqueName])
		self.removeItemLRU()
		self.lock.release()
		return res, item

	def _doAddCodeEdgeItem(self, srcUniqueName, tarUniqueName):
		key = (srcUniqueName, tarUniqueName)
		if self.edgeDict.get(key, None):
			return
		if srcUniqueName not in self.itemDict or tarUniqueName not in self.itemDict:
			return

		from ui.CodeUIEdgeItem import CodeUIEdgeItem
		item = CodeUIEdgeItem(srcUniqueName, tarUniqueName)
		self.edgeDict[key] = item
		self.addItem(item)

	def addCodeEdgeItem(self, srcUniqueName, tarUniqueName):
		self.lock.acquire()
		self._doAddCodeEdgeItem(srcUniqueName, tarUniqueName)
		self.lock.release()

	def _doDeleteCodeItem(self, uniqueName):
		node = self.itemDict.get(uniqueName, None)
		if not node:
			return

		deleteEdges = []
		for edgeKey in self.edgeDict.keys():
			if edgeKey[0] == uniqueName or edgeKey[1] == uniqueName:
				deleteEdges.append(edgeKey)

		for edgeKey in deleteEdges:
			self._doDeleteCodeEdgeItem(edgeKey)

		self.removeItem(node)
		del self.itemDict[uniqueName]

	def deleteCodeItem(self, uniqueName):
		self.lock.acquire()
		self._doDeleteCodeItem(uniqueName)
		self.deleteLRU([uniqueName])
		self.removeItemLRU()
		self.lock.release()

	def _doDeleteCodeEdgeItem(self, edgeKey):
		edge = self.edgeDict.get(edgeKey, None)
		if not edge:
			return
		self.removeItem(edge)
		del self.edgeDict[edgeKey]

	def deleteCodeEdgeItem(self, edgeKey):
		self.lock.acquire()
		self._doDeleteCodeEdgeItem(edgeKey)
		self.lock.release()

	def clearUnusedItems(self):
		self.lock.acquire()

		deleteList = []
		for itemKey, item in self.itemDict.items():
			item.displayScore -= 1
			if item.displayScore <= 0:
				deleteList.append(itemKey)

		print('delete list', deleteList)
		for deleteName in deleteList:
			self._doDeleteCodeItem(deleteName)

		self.deleteLRU(deleteList)

		self.itemLruQueue
		self.lock.release()

	def clearOldItem(self):
		if len(self.itemLruQueue) <= 0:
			return

		print('clear old item ------ begin')
		self.lock.acquire()
		print('lock ------------------')
		# deleteList = []
		# for itemKey, item in self.itemDict.items():
		# 	item.displayScore -= 1
		# 	if item.displayScore <= 0:
		# 		deleteList.append(itemKey)

		# print('delete list', deleteList)
		# for deleteName in deleteList:
		# 	self._doDeleteCodeItem(deleteName)
		# self.deleteLRU(deleteList)

		lastItem = self.itemLruQueue[-1]
		lastPos = self.itemDict[lastItem].pos()
		self._doDeleteCodeItem(lastItem)
		print('delte code item end')
		self.deleteLRU([lastItem])
		print('delete lru end ')
		self.lock.release()
		print('clear old item end ----------')

		if lastPos:
			self.selectNearestItem(lastPos)

	def deleteSelectedItems(self):
		self.lock.acquire()
		itemList = []
		lastPos = None
		for itemKey, item in self.itemDict.items():
			if item.isSelected():
				itemList.append(itemKey)
				lastPos = item.pos()

		for itemKey in itemList:
			self._doDeleteCodeItem(itemKey)
		self.deleteLRU(itemList)

		self.removeItemLRU()
		self.lock.release()

		# if lastPos:
		# 	self.selectNearestItem(lastPos)

	def getNode(self, uniqueName):
		node = self.itemDict.get(uniqueName, None)
		return node

	def findNeighbour(self, mainDirection = (1.0,0.0)):
		print('find neighbour begin', mainDirection)
		itemList = self.selectedItems()
		if not itemList:
			return

		import ui.CodeUIItem
		centerItem = itemList[0]
		minValEdged = 1.0e12
		minItemEdged = None
		minValUnedged = 1.0e12
		minItemUnedged = None
		for uname, item in self.itemDict.items():
			if item is centerItem:
				continue
			dPos = item.pos() - centerItem.pos()
			cosVal = (dPos.x() * mainDirection[0] + dPos.y() * mainDirection[1]) / \
					 math.sqrt(dPos.x()*dPos.x() + dPos.y()*dPos.y())
			if cosVal < 0.6:
				continue

			xProj = dPos.x()*mainDirection[0] + dPos.y()*mainDirection[1]
			yProj = dPos.x()*mainDirection[1] - dPos.y()*mainDirection[0]

			xProj /= 3.0
			dist = xProj * xProj + yProj * yProj

			# 检查与当前项是否有边连接
			isEdged = False
			for edgeKey in self.edgeDict.keys():
				if centerItem.getUniqueName() in edgeKey and uname in edgeKey:
					isEdged = True

			if isEdged:
				if dist < minValEdged:
					minValEdged = dist
					minItemEdged = item
			else:
				if dist < minValUnedged:
					minValUnedged = dist
					minItemUnedged = item

		# 优先采用有边连接的项
		minItem = None
		if minItemEdged and minItemUnedged:
			minItem = minItemEdged if minValEdged < minValUnedged * 2 else minItemUnedged
		elif minItemEdged:
			minItem = minItemEdged
		elif minItemUnedged:
			minItem = minItemUnedged
		#from UIManager import UIManager
		print('find nei', minItem)
		if minItem:
			self.selectOneItem(minItem)
			print('show in editor------')
			self.showInEditor()

	def selectOneItem(self, item):
		if not item:
			return
		self.clearSelection()
		item.setSelected(True)

		for view in self.views():
			view.centerOn(item)
			view.invalidateScene()

	def selectNearestItem(self, pos):
		minDist = 1e12
		minItem = None
		for uname, item in self.itemDict.items():
			dPos = item.pos() - pos
			dist = dPos.x() * dPos.x() + dPos.y() * dPos.y()
			if dist < minDist:
				minDist = dist
				minItem = item

		if minItem:
			self.selectOneItem(minItem)

	def showInEditor(self):
		itemList = self.selectedItems()
		print('item list', itemList)
		if not itemList:
			return

		item = itemList[0]
		entity = item.getEntity()
		print('entity', entity)
		if not entity:
			return

		from db.DBManager import DBManager
		refs = entity.refs('definein')
		for r in refs:
			print('r:', r.kindname(), r.ent().name(), r.ent().kindname())
		if not refs:
			return

		ref = refs[0]
		fileEnt = ref.file()
		line = ref.line()
		column = ref.column()
		fileName = fileEnt.longname()

		print('file ----', line, column, fileName, ref.kind(), ref.kindname())
		socket = DBManager.instance().getSocket()
		socket.remoteCall('goToPage', (fileName, line, column))

	def _addRefs(self, refStr, entStr, inverseEdge = False):
		from db.DBManager import DBManager
		dbObj = DBManager.instance().getDB()
		scene = self
		itemList = self.selectedItems()

		refNameList = []

		for item in itemList:
			uniqueName = item.getUniqueName()
			entNameList = dbObj.searchRefEntity(uniqueName, refStr, entStr)
			refNameList += entNameList
			for entName in entNameList:
				res, refItem = scene._doAddCodeItem(entName)
				if res:
					if refStr.find('callby') != -1:
						refItem.setPos(item.pos() + QtCore.QPointF(-50,random.uniform(-50,50)))
					elif refStr.find('call') != -1:
						refItem.setPos(item.pos() + QtCore.QPointF(50,random.uniform(-50,50)))
					else:
						refItem.setPos(item.pos() + QtCore.QPointF(random.uniform(-50,50),random.uniform(-50,50)))
				if inverseEdge:
					scene._doAddCodeEdgeItem(uniqueName, entName)
				else:
					scene._doAddCodeEdgeItem(entName, uniqueName)

		# for uname, item in self.itemDict.items():
		# 	# 再增加与现有节点的联系
		# 	allEntNameList = dbObj.searchRefEntity(uname, '', '', True)
		# 	for entName in allEntNameList:
		# 		if entName not in self.itemDict:
		# 			continue
		# 		inEdgeDict = False
		# 		for edgeKey in self.edgeDict.keys():
		# 			if entName in edgeKey and uname in edgeKey:
		# 				inEdgeDict = True
		# 				break
		# 		if inEdgeDict:
		# 			continue
		#
		# 		scene._doAddCodeEdgeItem(entName, uname)

		return refNameList


	def addRefs(self, refStr, entStr, inverseEdge = False):
		self.lock.acquire()
		refNameList = self._addRefs(refStr, entStr, inverseEdge)
		self.updateLRU(refNameList)
		self.removeItemLRU()
		self.lock.release()

	def updatePos(self):
		posList = [item.pos() for item in self.itemDict.values()]
		rList = [item.getRadius() for item in self.itemDict.values()]

		posDict = {}
		i = 0
		for itemName, item in self.itemDict.items():
			posDict[itemName] = i
			i+= 1

		nPos = len(posList)
		for i in range(nPos):
			posI = posList[i]
			rI = rList[i]
			for j in range(nPos):
				if i == j:
					continue
				posJ = posList[j]
				dp = posI - posJ
				dpLengthSq = dp.x()*dp.x() + dp.y()*dp.y()
				dpLength = math.sqrt(dpLengthSq)

				if dpLengthSq < 1e-3:
					continue

				force = max(1.0 / (dpLength+1.0) * 20 * math.sqrt(rI * rList[j]) - 1, 0)
				offset = dp * (1.0 / dpLength * force)
				posList[i] += offset
				posList[j] -= offset

		for edgeName in self.edgeDict.keys():
			i = posDict[edgeName[0]]
			j = posDict[edgeName[1]]
			posI = posList[i]
			posJ = posList[j]
			dp = posI - posJ
			dpLengthSq = dp.x()*dp.x() + dp.y()*dp.y()
			dpLength = math.sqrt(dpLengthSq)
			if dpLength < 1e-3:
				continue

			force = dpLength * 0.1
			offset = dp * (1.0 / dpLength * force)
			posList[i] = posI - offset
			posList[j] = posJ + offset

		#print('-------- result -------- ')
		i=0
		for itemName, item in self.itemDict.items():
			item.setPos(posList[i])
			#print(posList[i])
			i += 1

	@QtCore.pyqtSlot()
	def onSelectItems(self):
		#print( 'on select items')
		itemList = self.selectedItems()

		for item in itemList:
			uniqueName = item.getUniqueName()
			self.updateLRU([uniqueName])

		self.removeItemLRU()
