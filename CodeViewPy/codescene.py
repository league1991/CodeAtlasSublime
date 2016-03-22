# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtCore, QtGui, uic, Qt
import math
import random
import sys
import traceback
import threading
import time

#class SceneUpdateThread(threading.Thread):
class SceneUpdateThread(QtCore.QThread):
	def __init__(self, scene, lock):
		#threading.Thread.__init__(self)
		super(SceneUpdateThread, self).__init__()
		self.scene = scene
		self.lock = lock
		self.isActive = True

		self.itemSet = set()
		self.edgeNum = 0

	def setActive(self, isActive):
		self.lock.acquire()
		self.isActive = isActive
		self.lock.release()

	def run(self):
		#print('run qthread')
		while True:
			if self.isActive:
				#print('acquire lock')
				self.lock.acquire()
				#print('update thread -----------------------------------------', self.lock, self.scene.lock)
				#self.updatePos()
				if self.itemSet != set(self.scene.itemDict.keys()) or self.edgeNum != len(self.scene.edgeDict):
					#print('before update layout')
					self.updateLayeredLayoutWithComp()
				#print('before move items')
				self.moveItems()
				self.updateCallOrder()
				#print('before invalidate scene')
				#self.scene.invalidate()
				self.lock.release()
				self.scene.update()
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
				dpLengthSq = dp.x()*dp.x() + dp.y()*dp.y()+1e-5
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
			dpLength = math.sqrt(dpLengthSq)+1e-5
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

	def updateLayeredLayoutWithComp(self): 
		class Vtx(object):
			def __init__(self, name, idx, radius = 1):
				self.inNodes = set()
				self.outNodes = set()
				self.name = name
				self.idx = idx
				self.comp = None
				self.compIdx = None
				self.pos = None
				self.radius = radius

		if len(self.scene.itemDict) == 0:
			return
		vtxName2Id = {}
		vtxList = []
		edgeList = []
		for name, item in self.scene.itemDict.items():
			ithVtx = len(vtxList)
			vtxList.append(Vtx(name, ithVtx, item.getRadius()))
			vtxName2Id[name] = ithVtx

		for edgeKey, edge in self.scene.edgeDict.items():
			v1 = vtxName2Id[edgeKey[0]]
			v2 = vtxName2Id[edgeKey[1]]
			vtxList[v1].outNodes.add(v2)
			vtxList[v2].inNodes.add(v1)
			edgeList.append((v1,v2))

		#print('vtx list', vtxList)
		#print('edge list', edgeList)

		remainSet = set([i for i in range(len(vtxList))])
		compList = []   # [[idx1,idx2,...],[...]]
		while len(remainSet) > 0:
			# 找出剩余一个顶点并加入队列
			ids = [list(remainSet)[0]]
			ithComp = len(compList)
			vtxList[ids[0]].comp = ithComp
			compMap = []
			# 遍历一个连通分量
			while len(ids) > 0:
				newIds = []
				for id in ids:
					# 把一个顶点加入连通分量
					vtx = vtxList[id]
					vtx.compIdx = len(compMap)
					compMap.append(id)
					# 把周围未遍历顶点加入队列
					for inId in vtx.inNodes:
						inVtx = vtxList[inId]
						if inVtx.comp is None:
							inVtx.comp = ithComp
							newIds.append(inId)
					for outId in vtx.outNodes:
						outVtx = vtxList[outId]
						if outVtx.comp is None:
							outVtx.comp = ithComp
							newIds.append(outId)
					remainSet.discard(id)
				ids = newIds
			# 增加一个完整的连通分量
			compList.append(compMap)

		#print('comp list', compList)
		from grandalf.graphs import Vertex, Edge, Graph
		class VtxView(object):
			def __init__(self, w, h):
				self.w = w
				self.h = h

		# 构造每个连通分量的图结构
		offset = (0,0)
		bboxMin = [1e6,1e6]
		bboxMax = [-1e6,-1e6]
		for ithComp, compMap in enumerate(compList):
			minPnt = [1e6,1e6]
			maxPnt = [-1e6,-1e6]

			# 构造图数据并布局
			V = []
			for oldId in compMap:
				r = vtxList[oldId].radius
				vtx = Vertex(oldId)
				height = len(vtxList[oldId].name) * 0.9 + 2
				vtx.view = VtxView(r*2.0, max(r*2.0,height))
				V.append(vtx)
 
			E = []  
			for edgeKey in edgeList:
				if vtxList[edgeKey[0]].comp == ithComp:
					E.append(Edge(V[vtxList[edgeKey[0]].compIdx], V[vtxList[edgeKey[1]].compIdx]))

			#print('V', len(V))
			#print('E', E)

			g = Graph(V,E)
			from grandalf.layouts import SugiyamaLayout
			packSpace = 4
			sug = SugiyamaLayout(g.C[0])
			sug.xspace = packSpace
			sug.yspace = packSpace
			sug.order_iter = 16
			sug.init_all()
			sug.draw(5)

			# 统计包围盒
			for v in g.C[0].sV:
				oldV = vtxList[v.data]
				x= v.view.xy[1]
				y= v.view.xy[0]
				oldV.pos = (x,y)
				minPnt[0] = min(minPnt[0],x)
				minPnt[1] = min(minPnt[1],y-oldV.radius)
				maxPnt[0] = max(maxPnt[0],x)
				maxPnt[1] = max(maxPnt[1],y+oldV.radius)

			#print('bbox', minPnt, maxPnt)
			for v in g.C[0].sV:
				oldV = vtxList[v.data]
				newPos = (oldV.pos[0]-minPnt[0]+offset[0], oldV.pos[1]-minPnt[1]+offset[1])
				self.scene.itemDict[oldV.name].setTargetPos(QtCore.QPointF(newPos[0], newPos[1]))
				bboxMin[0] = min(bboxMin[0], newPos[0])
				bboxMin[1] = min(bboxMin[1], newPos[1])
				bboxMax[0] = max(bboxMax[0], newPos[0])
				bboxMax[1] = max(bboxMax[1], newPos[1])

			offset = (offset[0], offset[1]+maxPnt[1]-minPnt[1]+packSpace)
			#print('offset', offset)

		# 设置四个角的item
		cornerList = self.scene.cornerItem
		mar = 300
		cornerList[0].setPos(bboxMin[0]-mar, bboxMin[1]-mar)
		cornerList[1].setPos(bboxMin[0]-mar, bboxMax[1]+mar)
		cornerList[2].setPos(bboxMax[0]+mar, bboxMin[1]-mar)
		cornerList[3].setPos(bboxMax[0]+mar, bboxMax[1]+mar)

		# 更新标志数据
		self.itemSet = set(self.scene.itemDict.keys())
		self.edgeNum = len(self.scene.edgeDict)

	def updateCallOrder(self):
		import ui.CodeUIItem
		import ui.CodeUIEdgeItem

		for key, edge in self.scene.edgeDict.items():
			edge.orderData = None

		item = self.scene.selectedItems()
		if not item:
			return
		item = item[0]
		if isinstance(item, ui.CodeUIEdgeItem.CodeUIEdgeItem):
			item = self.scene.itemDict.get(item.srcUniqueName, None)
		if not item or item.kind != ui.CodeUIItem.ITEM_FUNCTION:
			return

		edgeList = []
		xRange = [1e6, -1e6]
		for key, edge in self.scene.edgeDict.items():
			if key[0] == item.getUniqueName() and self.scene.itemDict[key[1]].kind == ui.CodeUIItem.ITEM_FUNCTION:
				edgeList.append(edge)
				srcPos, tarPos = edge.getNodePos()
				xRange[0] = min(tarPos.x(), xRange[0])
				xRange[1] = max(tarPos.x(), xRange[1])
		if not edgeList:
			return

		basePos = 0
		stepSize = 0
		itemX = item.pos().x()
		if xRange[0] < itemX and xRange[1] > itemX:
			stepSize = 0
			basePos = None
		elif xRange[0] >= itemX:
			stepSize = -10
			basePos = xRange[0]
		elif xRange[1] <= itemX:
			stepSize = 10
			basePos = xRange[1]

		edgeList.sort(key = lambda edge: edge.line + edge.column / 1000.0)

		#print('edge item list', edgeList)

		nEdge = len(edgeList)
		for i, edge in enumerate(edgeList):
			srcPos, tarPos = edge.getNodePos()
			padding = -20.0 if srcPos.x() < tarPos.x() else 20.0
			if basePos is None:
				x = tarPos.x() + padding
				y = edge.findCurveYPos(x)
				edge.orderData = (i+1, QtCore.QPointF(x,y))
			else:
				x = basePos + padding + stepSize * (nEdge-i-1)
				y = edge.findCurveYPos(x)
				edge.orderData = (i+1, QtCore.QPointF(x,y))


	def moveItems(self):
		#print('move items')
		pos = QtCore.QPointF(0,0)
		nSelected = 0
		bboxMin = [1e6, 1e6]
		bboxMax = [-1e6, -1e6]
		for name, item in self.scene.itemDict.items():
			item.moveToTarget(0.1)
			if item.isSelected():
				pos += item.pos()
				nSelected+=1
			newPos = item.pos()
			bboxMin[0] = min(bboxMin[0], newPos.x())
			bboxMin[1] = min(bboxMin[1], newPos.y())
			bboxMax[0] = max(bboxMax[0], newPos.x())
			bboxMax[1] = max(bboxMax[1], newPos.y())
			#print('offset', offset)

		for name, item in self.scene.edgeDict.items():
			item.buildPath()
			if item.isSelected():
				pos += item.getMiddlePos()
				nSelected+=1

		# 设置四个角的item
		if bboxMax[0] > bboxMin[0] and bboxMax[1] > bboxMin[1]:
			cornerList = self.scene.cornerItem
			mar = 300
			cornerList[0].setPos(bboxMin[0]-mar, bboxMin[1]-mar)
			cornerList[1].setPos(bboxMin[0]-mar, bboxMax[1]+mar)
			cornerList[2].setPos(bboxMax[0]+mar, bboxMin[1]-mar)
			cornerList[3].setPos(bboxMax[0]+mar, bboxMax[1]+mar)

		for view in self.scene.views():
			pos = self.scene.getSelectedCenter()
			if getattr(view, 'centerPnt', None):
				view.centerPnt = view.centerPnt * 0.97 + pos * 0.03
				view.centerOn(view.centerPnt) 
		# if nSelected:
		# 	pos /= float(nSelected)

			#self.centerPnt = self.centerPnt * 0.95 + pos * 0.05
			# for view in self.scene.views():
			# 	view.centerOn(self.centerPnt)

class RecursiveLock(QtCore.QMutex):
	def __init__(self):
		super(QtCore.QMutex, self).__init__(QtCore.QMutex.Recursive)

	def acquire(self):
		self.lock()

	def release(self):
		self.unlock()

class CodeScene(QtGui.QGraphicsScene):
	def __init__(self, *args):
		super(CodeScene, self).__init__(*args)
		self.itemDict = {}
		self.edgeDict = {}
		self.itemLruQueue = []
		self.lruMaxLength = 50

		self.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
		#self.lock = threading.RLock()
		#self.lock = QtCore.QSemaphore(1)
		self.lock = RecursiveLock()
		self.updateThread = SceneUpdateThread(self, self.lock)
		self.updateThread.start()

		self.cornerItem = []
		for i in range(4):
			item = QtGui.QGraphicsRectItem(0,0,5,5)
			item.setPen(QtGui.QPen(QtGui.QColor(0,0,0,0)))
			item.setBrush(QtGui.QBrush())
			self.cornerItem.append(item)
			self.addItem(item)
		self.connect(self, QtCore.SIGNAL('selectionChanged()'), self, QtCore.SLOT('onSelectItems()'))

	def event(self, eventObj):
		#print('CodeScene. event', self, eventObj)
		if getattr(self, 'lock', None):
			self.lock.acquire()
			res = super(CodeScene, self).event(eventObj)
			self.lock.release()
			return res
		return super(CodeScene, self).event(eventObj)

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
		# print('------------- update lru -------------')
		# for i, key in enumerate(self.itemLruQueue):
		# 	print(i, self.itemDict[key].name)
		# print('--------------------------------------')
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
	def getSelectedCenter(self):
		pos = QtCore.QPointF(0,0)
		nSelected = 0
		for name, item in self.itemDict.items():
			if item.isSelected():
				pos += item.pos()
				nSelected+=1

		for name, item in self.edgeDict.items():
			if item.isSelected():
				pos += item.getMiddlePos()
				nSelected+=1

		if nSelected:
			pos /= float(nSelected)
		return pos

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
		off = 0.03
		offsetPnt = QtCore.QPointF(random.uniform(-off,off), random.uniform(-off,off))
		item.setPos(self.getSelectedCenter() + offsetPnt)
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

	def _doAddCodeEdgeItem(self, srcUniqueName, tarUniqueName, refObj):
		key = (srcUniqueName, tarUniqueName)
		if self.edgeDict.get(key, None):
			return
		if srcUniqueName not in self.itemDict or tarUniqueName not in self.itemDict:
			return

		from ui.CodeUIEdgeItem import CodeUIEdgeItem
		item = CodeUIEdgeItem(srcUniqueName, tarUniqueName, dbRef=refObj)
		self.edgeDict[key] = item
		self.addItem(item)

	# def addCodeEdgeItem(self, srcUniqueName, tarUniqueName):
	# 	self.lock.acquire()
	# 	self._doAddCodeEdgeItem(srcUniqueName, tarUniqueName)
	# 	self.lock.release()

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

		print('acquire lock -----------------------------------------', self.lock)

		itemList = []
		lastPos = None
		for itemKey, item in self.itemDict.items():
			if item.isSelected():
				itemList.append(itemKey)
				lastPos = item.pos()

		if itemList:
			print('do delete code item')
			for itemKey in itemList:
				self._doDeleteCodeItem(itemKey)
			print('delete lru')
			self.deleteLRU(itemList)
			print('remove item lru')
			self.removeItemLRU()

		if lastPos:
			print('select nearest item')
			self.selectNearestItem(QtCore.QPointF(lastPos.x(), lastPos.y()))

		print('before release')
		self.lock.release()
		print('release lock -----------------------------------------', self.lock)

	def getNode(self, uniqueName):
		node = self.itemDict.get(uniqueName, None)
		return node

	def findNeighbour(self, mainDirection = (1.0,0.0)):
		print('find neighbour begin', mainDirection)
		itemList = self.selectedItems()
		if not itemList:
			print('no item', itemList)
			return

		from ui.CodeUIItem import CodeUIItem
		from ui.CodeUIEdgeItem import CodeUIEdgeItem
		centerItem = itemList[0]
		centerIsNode = isinstance(centerItem, CodeUIItem)
		if centerIsNode:
			minItem = self.findNeighbourForNode(centerItem, mainDirection)
		else:
			minItem = self.findNeighbourForEdge(centerItem, mainDirection)

		#from UIManager import UIManager
		print('find nei', minItem)
		if minItem:
			if self.selectOneItem(minItem):
				print('show in editor------')
				self.showInEditor()

	def findNeighbourForEdge(self, centerItem, mainDirection):
		from ui.CodeUIItem import CodeUIItem
		from ui.CodeUIEdgeItem import CodeUIEdgeItem
		centerPos = centerItem.getMiddlePos()

		srcPos, tarPos = centerItem.getNodePos()
		edgeDir = tarPos - srcPos
		edgeDir /= math.sqrt(edgeDir.x()*edgeDir.x() + edgeDir.y()*edgeDir.y() + 1e-5)
		proj = mainDirection[0]*edgeDir.x() + mainDirection[1]*edgeDir.y()
 
		srcNode = self.getNode(centerItem.srcUniqueName)
		tarNode = self.getNode(centerItem.tarUniqueName)

		if math.fabs(mainDirection[0]) > 0.8:			
			if proj > 0.1 and tarNode:
				print('tar node----------------')
				return tarNode
			elif proj < -0.1 and srcNode:
				print('src node---------------')
				return srcNode

		# 找出最近的边
		minEdgeVal = 1.0e12
		minEdge = None
		for edgeKey, item in self.edgeDict.items():
			if item is centerItem:
				continue
			dPos = item.getMiddlePos() - centerPos
			cosVal = (dPos.x() * mainDirection[0] + dPos.y() * mainDirection[1]) / \
					 math.sqrt(dPos.x()*dPos.x() + dPos.y()*dPos.y()+1e-5)
			#print('cosVal', cosVal, item.getMiddlePos(), dPos)
			if cosVal < 0.2:
				continue
			xProj = dPos.x()*mainDirection[0] + dPos.y()*mainDirection[1]
			yProj = dPos.x()*mainDirection[1] - dPos.y()*mainDirection[0]

			xProj /= 2.0
			dist = xProj * xProj + yProj * yProj
			if dist < minEdgeVal:
				minEdgeVal = dist
				minEdge = item

		print('min edge val', minEdgeVal, minEdge)
		# 找出最近的节点
		minNodeValConnected = 1.0e12
		minNodeConnected = None
		minNodeVal = 1.0e12
		minNode = None
		for uname, item in self.itemDict.items():
			if item is centerItem:
				continue
			dPos = item.pos() - centerPos
			cosVal = (dPos.x() * mainDirection[0] + dPos.y() * mainDirection[1]) / \
					 math.sqrt(dPos.x()*dPos.x() + dPos.y()*dPos.y()+1e-5)
			if cosVal < 0.6:
				continue

			xProj = dPos.x()*mainDirection[0] + dPos.y()*mainDirection[1]
			yProj = dPos.x()*mainDirection[1] - dPos.y()*mainDirection[0]

			xProj /= 2.0
			dist = xProj * xProj + yProj * yProj

			# 检查与当前边是否连接
			isEdged = False
			if item in (centerItem.srcUniqueName, centerItem.tarUniqueName):
				isEdged = True

			if isEdged:
				if dist < minNodeValConnected:
					minNodeValConnected = dist
					minNodeConnected = item
			else:
				if dist < minNodeVal:
					minNodeVal = dist
					minNode = item

		minEdgeVal *= 3
		minNodeVal *= 2

		valList = [minEdgeVal,  minNodeVal, minNodeValConnected]
		itemList =[minEdge, minNode, minNodeConnected]
		minItem = None
		minItemVal = 1e12
		for i in range(len(valList)):
			if valList[i] < minItemVal:
				minItemVal = valList[i]
				minItem = itemList[i]

		return minItem

	def findNeighbourForNode(self, centerItem, mainDirection):
		from ui.CodeUIItem import CodeUIItem
		from ui.CodeUIEdgeItem import CodeUIEdgeItem
		centerPos = centerItem.pos()

		# 找出最近的边
		minEdgeValConnected = 1.0e12
		minEdgeConnected = None
		minEdgeVal = 1.0e12
		minEdge = None
		for edgeKey, item in self.edgeDict.items():
			dPos = item.getMiddlePos() - centerPos
			cosVal = (dPos.x() * mainDirection[0] + dPos.y() * mainDirection[1]) / \
					 math.sqrt(dPos.x()*dPos.x() + dPos.y()*dPos.y()+1e-5)
			#print('cosVal', cosVal, item.getMiddlePos(), dPos)
			if cosVal < 0.2:
				continue
			xProj = dPos.x()*mainDirection[0] + dPos.y()*mainDirection[1]
			yProj = dPos.x()*mainDirection[1] - dPos.y()*mainDirection[0]

			xProj /= 3.0
			dist = xProj * xProj + yProj * yProj
			if centerItem.getUniqueName() in edgeKey:
				if dist < minEdgeValConnected:
					minEdgeValConnected = dist
					minEdgeConnected = item
			else:
				if dist < minEdgeVal:
					minEdgeVal = dist
					minEdge = item

		print('min edge val', minEdgeVal, minEdge)
		# 找出最近的节点
		minNodeValConnected = 1.0e12
		minNodeConnected = None
		minNodeVal = 1.0e12
		minNode = None
		for uname, item in self.itemDict.items():
			if item is centerItem:
				continue
			dPos = item.pos() - centerPos
			cosVal = (dPos.x() * mainDirection[0] + dPos.y() * mainDirection[1]) / \
					 math.sqrt(dPos.x()*dPos.x() + dPos.y()*dPos.y()+1e-5)
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
				if dist < minNodeValConnected:
					minNodeValConnected = dist
					minNodeConnected = item
			else:
				if dist < minNodeVal:
					minNodeVal = dist
					minNode = item

		minEdgeVal *= 3
		minNodeVal *= 2

		valList = [minEdgeVal, minEdgeValConnected, minNodeVal, minNodeValConnected]
		itemList =[minEdge, minEdgeConnected, minNode, minNodeConnected]
		minItem = None
		minItemVal = 1e12
		for i in range(len(valList)):
			if valList[i] < minItemVal:
				minItemVal = valList[i]
				minItem = itemList[i]

		return minItem
		# if minEdge and minEdgeVal < min(minValEdged, minValUnedged):
		# 	minItem = minEdge
		# elif minItemEdged and minItemUnedged:
		# 	minItem = minItemEdged if minValEdged < minValUnedged else minItemUnedged
		# elif minItemEdged:
		# 	minItem = minItemEdged
		# elif minItemUnedged:
		# 	minItem = minItemUnedged

	def selectOneItem(self, item):
		if not item:
			return False
		item.setSelected(True)
		if item.isSelected():
			self.clearSelection()
			item.setSelected(True)
			return True
		else:
			item.setSelected(False)
			return False

		# for view in self.views():
		# 	view.centerOn(item)
		# 	view.invalidateScene()

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
			return self.selectOneItem(minItem)
		else:
			return False

	def showInEditor(self):
		from ui.CodeUIItem import CodeUIItem
		from ui.CodeUIEdgeItem import CodeUIEdgeItem
		print('----------------import')
		itemList = self.selectedItems()
		print('item list', itemList)
		if not itemList:
			return
 
		item = itemList[0]
		if isinstance(item, CodeUIItem):
			entity = item.getEntity()
			print('entity', entity)
			if not entity:
				return

			refs = entity.refs('definein')
			# for r in refs:
			# 	print('r:', r.kindname(), r.ent().name(), r.ent().kindname())
			if not refs:
				return

			ref = refs[0]
			fileEnt = ref.file()
			line = ref.line()
			column = ref.column()
			fileName = fileEnt.longname()
			print('file ----', line, column, fileName, ref.kind(), ref.kindname())
		elif isinstance(item, CodeUIEdgeItem):
			line = item.line
			column = item.column
			fileName = item.file

		from db.DBManager import DBManager
		socket = DBManager.instance().getSocket()
		socket.remoteCall('goToPage', (fileName, line, column))

	def _addRefs(self, refStr, entStr, inverseEdge = False):
		from db.DBManager import DBManager
		from ui.CodeUIItem import CodeUIItem
		dbObj = DBManager.instance().getDB()
		scene = self
		itemList = self.selectedItems()

		refNameList = []


		for item in itemList:
			if not isinstance(item, CodeUIItem):
				continue
			uniqueName = item.getUniqueName()
			entNameList, refList = dbObj.searchRefEntity(uniqueName, refStr, entStr)
			refNameList += entNameList
			for ithRef, entName in enumerate(entNameList):
				refObj = refList[ithRef]
				res, refItem = scene._doAddCodeItem(entName)
				# if res:
				# 	if refStr.find('callby') != -1:
				# 		refItem.setPos(item.pos() + QtCore.QPointF(-50,random.uniform(-50,50)))
				# 	elif refStr.find('call') != -1:
				# 		refItem.setPos(item.pos() + QtCore.QPointF(50,random.uniform(-50,50)))
				# 	else:
				# 		refItem.setPos(item.pos() + QtCore.QPointF(random.uniform(-50,50),random.uniform(-50,50)))
				if inverseEdge:
					scene._doAddCodeEdgeItem(uniqueName, entName, refObj)
				else:
					scene._doAddCodeEdgeItem(entName, uniqueName, refObj)

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
				dpLengthSq = dp.x()*dp.x() + dp.y()*dp.y()+1e-5
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
		from ui.CodeUIItem import CodeUIItem
		from ui.CodeUIEdgeItem import CodeUIEdgeItem
		#print( 'on select items')
		itemList = self.selectedItems()

		for item in itemList:
			if not isinstance(item, CodeUIItem):
				continue
			uniqueName = item.getUniqueName()
			self.updateLRU([uniqueName])

		self.removeItemLRU()
