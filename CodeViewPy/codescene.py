# -*- coding: utf-8 -*-
import sys
import os
from PyQt4 import QtCore, QtGui, uic, Qt
import math
import random
import sys
import traceback
import threading
import time
import hashlib
from json import *

#class SceneUpdateThread(threading.Thread):
class SceneUpdateThread(QtCore.QThread):
	updateSignal = QtCore.pyqtSignal()
	def __init__(self, scene, lock):
		#threading.Thread.__init__(self)
		super(SceneUpdateThread, self).__init__()
		self.scene = scene
		self.lock = lock
		self.isActive = True

		self.itemSet = set()
		self.edgeNum = 0
		print(self.updateSignal)
		self.updateSignal.connect(self.scene.update, Qt.Qt.QueuedConnection)

	def setActive(self, isActive):
		self.lock.acquire()
		self.isActive = isActive
		self.lock.release()

	def run(self):
		#print('run qthread')
		while True:
			if self.isActive:
				#print('acquire lock')
				#self.lock.acquire()
				self.scene.acquireLock()
				#print('update thread begin -----------------------------------------')
				#self.updatePos()
				if self.itemSet != set(self.scene.itemDict.keys()) or self.edgeNum != len(self.scene.edgeDict):
					#print('before update layout')
					self.updateLayeredLayoutWithComp()
				#print('before move items')
				self.moveItems()
				#print('before call order')
				self.updateCallOrder()
				self.scene.updateCurrentValidScheme()
				#print('before invalidate scene')
				#self.scene.invalidate()
				#print('before update scene')
				#self.scene.update()
				self.updateSignal.emit()
				#print('update thread end -----------------------------------------')
				#self.lock.release()
				self.scene.releaseLock()
				#print('lock release')
			#time.sleep(0.08)
			self.msleep(60)
			#print('sleep')

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
			def __init__(self, name, idx, radius = 1, height = 1):
				self.inNodes = set()
				self.outNodes = set()
				self.name = name
				self.idx = idx
				self.comp = None
				self.compIdx = None
				self.pos = None
				self.radius = radius
				self.fontHeight = height
				self.height = max(radius*2, height)
				self.firstKey = 0.0
				self.secondKey = 0.0
				self.thirdKey = 0.0

		if len(self.scene.itemDict) == 0:
			return
		vtxName2Id = {}
		vtxList = []
		edgeList = []
		for name, item in self.scene.itemDict.items():
			ithVtx = len(vtxList)
			v = Vtx(name, ithVtx, item.getRadius(), item.getHeight())
			v.dispName = item.name
			vtxList.append(v)
			vtxName2Id[name] = ithVtx

		for edgeKey, edge in self.scene.edgeDict.items():
			v1 = self.scene.itemDict[edgeKey[0]]
			v2 = self.scene.itemDict[edgeKey[1]]
			if v1.isFunction() and v2.isFunction():
				vtx2 = vtxList[vtxName2Id[edgeKey[1]]]
				vtx2.firstKey = hash(edge.file)
				vtx2.secondKey = edge.line
				vtx2.thirdKey = edge.column

		for edgeKey, edge in self.scene.edgeDict.items():
			v1 = vtxName2Id[edgeKey[0]]
			v2 = vtxName2Id[edgeKey[1]]
			vtxList[v1].outNodes.add(v2)
			vtxList[v2].inNodes.add(v1)
			edgeList.append((v1,v2))

		#print('vtx list', vtxList)
		#print('edge list', edgeList)

		# 构造连通分量
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

			# 按节点被调用顺序排序, 没有用
			# print('comp before sort', compMap)
			# compMap.sort(key = lambda vid: vtxList[vid].secondKey + vtxList[vid].thirdKey / 200.0)
			# for i, vid in enumerate(compMap):
			# 	vtxList[vid].compIdx = i
			# 	print(vtxList[vid].dispName, i)
			# print('comp after sort', compMap)
			# 增加一个连通分量
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
				w = vtxList[oldId].height
				vtx = Vertex(oldId)
				height = 170#len(vtxList[oldId].name) * 1.0 + 1
				#print('height--------', height)
				vtx.view = VtxView(w, height)
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
				minPnt[1] = min(minPnt[1],y-oldV.height*0.5)
				maxPnt[0] = max(maxPnt[0],x)
				maxPnt[1] = max(maxPnt[1],y+oldV.height*0.5)

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
		#print('update call order')
		for key, edge in self.scene.edgeDict.items():
			edge.orderData = None
			edge.isConnectedToFocusNode = False
		for key, node in self.scene.itemDict.items():
			node.isConnectedToFocusNode = False

		item = self.scene.selectedItems()
		#print('item', item)
		if not item:
			return
		item = item[0]
		isEdgeSelected = False
		if isinstance(item, ui.CodeUIEdgeItem.CodeUIEdgeItem):
			#print('not ui item')
			srcItem = self.scene.itemDict.get(item.srcUniqueName, None)
			dstItem = self.scene.itemDict.get(item.tarUniqueName, None)
			isEdgeSelected = True
			if srcItem and dstItem:
				srcItem.isConnectedToFocusNode = dstItem.isConnectedToFocusNode = True
			item = srcItem
		if not item or item.kind != ui.CodeUIItem.ITEM_FUNCTION:
			#print('not function')
			return

		#print('edge list')
		edgeList = []
		xRange = [1e6, -1e6]
		itemUniqueName = item.getUniqueName()
		for key, edge in self.scene.edgeDict.items():
			if key[0] == itemUniqueName and self.scene.itemDict[key[1]].kind == ui.CodeUIItem.ITEM_FUNCTION:
				edgeList.append(edge)
				srcPos, tarPos = edge.getNodePos()
				xRange[0] = min(tarPos.x(), xRange[0])
				xRange[1] = max(tarPos.x(), xRange[1])
			edge.isConnectedToFocusNode = itemUniqueName in key

			if not isEdgeSelected:
				if key[0] == itemUniqueName and self.scene.itemDict[key[1]].kind == ui.CodeUIItem.ITEM_FUNCTION:
					self.scene.itemDict[key[1]].isConnectedToFocusNode = True
				if key[1] == itemUniqueName and self.scene.itemDict[key[0]].kind == ui.CodeUIItem.ITEM_FUNCTION:
					self.scene.itemDict[key[0]].isConnectedToFocusNode = True

		if len(edgeList) <= 1:
			return
		#print('edge list2', edgeList)
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
		levelSize = int(nEdge / 6) + 1
		for i, edge in enumerate(edgeList):
			srcPos, tarPos = edge.getNodePos()
			padding = -8.0 if srcPos.x() < tarPos.x() else 8.0
			if basePos is None:
				x = tarPos.x() + padding
				y = edge.findCurveYPos(x)
				edge.orderData = (i+1, QtCore.QPointF(x,y))
			else:
				x = basePos + padding + stepSize * int((nEdge-i-1) / levelSize)
				y = edge.findCurveYPos(x)
				edge.orderData = (i+1, QtCore.QPointF(x,y))
		#print('update call end')

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

		if self.scene.isAutoFocus() and self.scene.getNSelected() > 0:
			for view in self.scene.views():
				pos = self.scene.getSelectedCenter()
				posView = view.mapFromScene(pos)
				xRatio = float(posView.x()) / view.width()
				yRatio = float(posView.y()) / view.height()
				# print('xratio', xRatio, yRatio)
				isInSafeRegion = xRatio > 0.3 and xRatio < 0.7 and yRatio > 0.2 and yRatio < 0.8
				if getattr(view, 'centerPnt', None) is not None and not isInSafeRegion:
					#print('view center', view.centerPnt)
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
		self.stopItem = {}		# 不显示的符号
		self.scheme = {}		# 保存的call graph
		self.curValidScheme = []# 选中物体有关的scheme
		self.curValidSchemeColor = []
		self.itemLruQueue = []
		self.lruMaxLength = 50

		self.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
		#self.lock = threading.RLock()
		#self.lock = QtCore.QSemaphore(1)
		self.lock = RecursiveLock()
		self.updateThread = SceneUpdateThread(self, self.lock)
		self.updateThread.start()

		self.cornerItem = []
		self.autoFocus = True
		self.autoFocusToggle = True
		for i in range(4):
			item = QtGui.QGraphicsRectItem(0,0,5,5)
			item.setPen(QtGui.QPen(QtGui.QColor(0,0,0,0)))
			item.setBrush(QtGui.QBrush())
			self.cornerItem.append(item)
			self.addItem(item)
		self.connect(self, QtCore.SIGNAL('selectionChanged()'), self, QtCore.SLOT('onSelectItems()'))

	# 添加或修改call graph
	def addOrReplaceScheme(self, name):
		nodes = [uname for uname, item in self.itemDict.items() if item.isSelected()]
		if not nodes:
			return
		def bothNodesSelected(edge):
			srcItem = self.itemDict.get(edge.srcUniqueName)
			tarItem = self.itemDict.get(edge.tarUniqueName)
			if not srcItem or not tarItem:
				return False
			return srcItem.isSelected() and tarItem.isSelected()
		edges = [edgePair for edgePair, item in self.edgeDict.items() if bothNodesSelected(item)]
		self.scheme[name] = {'node': nodes, 'edge':edges}

	def getSchemeNameList(self):
		return [name for name, schemeData in self.scheme.items()]

	def deleteScheme(self, name):
		if name in self.scheme:
			del self.scheme[name]

	def showScheme(self, name):
		if name not in self.scheme:
			return False

		self.clearSelection()
		from db.DBManager import DBManager
		dbObj = DBManager.instance().getDB()
		codeItemList = self.scheme[name].get('node',[])
		for uname in codeItemList:
			res, item = self.addCodeItem(uname)
			if item:
				item.setSelected(True)

		edgeItemList = self.scheme[name].get('edge',[])
		for edgePair in edgeItemList:
			refObj = dbObj.searchRefObj(edgePair[0], edgePair[1])
			if refObj:
				self._doAddCodeEdgeItem(edgePair[0], edgePair[1], refObj)
			edgeItem = self.edgeDict.get(edgePair)
			if edgeItem:
				edgeItem.setSelected(True)

	def showIthScheme(self, ithScheme):
		if ithScheme < 0 or ithScheme >= len(self.curValidScheme):
			return
		name = self.curValidScheme[ithScheme]
		self.showScheme(name)

	def getCurrentSchemeList(self):
		return self.curValidScheme

	def getCurrentSchemeColorList(self):
		return self.curValidSchemeColor

	def updateCurrentValidScheme(self):
		schemeNameSet = set()
		for uname, item in self.itemDict.items():
			if item.isSelected():
				for schemeName, schemeData in self.scheme.items():
					if uname in schemeData['node']:
						schemeNameSet.add(schemeName)

		for uname, item in self.edgeDict.items():
			item.schemeColorList = []
			if item.isSelected():
				for schemeName, schemeData in self.scheme.items():
					if uname in schemeData['edge']:
						schemeNameSet.add(schemeName)

		self.curValidScheme = list(schemeNameSet)
		self.curValidScheme.sort()
		self.curValidScheme = self.curValidScheme[0:9]
		self.curValidSchemeColor = []

		def schemeName2color(name):
			hashVal = int(hashlib.md5(name.encode("utf8")).hexdigest(),16) & 0xffffffff
			h = (hashVal & 0xff) / 255.0
			s = ((hashVal >> 8) & 0xff) / 255.0
			l = ((hashVal >> 16)& 0xff) / 255.0
			#return QtGui.QColor.fromHslF(h,s * 0.3 + 0.4,l * 0.4 + 0.5)
			return QtGui.QColor.fromHslF(h, 0.7+s*0.3, 0.4+l*0.2)

		for schemeName in self.curValidScheme:
			schemeData = self.scheme[schemeName]
			schemeColor = schemeName2color(schemeName)
			self.curValidSchemeColor.append(schemeColor)
			for edgePair in schemeData['edge']:
				edge = self.edgeDict.get(edgePair, None)
				if edge:
					edge.schemeColorList.append(schemeColor)


	# 添加不显示的符号
	def addForbiddenSymbol(self):
		for itemKey, item in self.itemDict.items():
			if item.isSelected():
				self.stopItem[item.getUniqueName()] = item.name

	def getForbiddenSymbol(self):
		return self.stopItem

	def deleteForbiddenSymbol(self, uname):
		if uname in self.stopItem:
			print('delete forbidden--', uname)
			del self.stopItem[uname]

	def onOpenDB(self):
		print('open db-----------------')
		from db.DBManager import DBManager
		dbObj = DBManager.instance().getDB()
		dbPath = dbObj.getDBPath()
		if not dbPath:
			return

		configPath = dbPath + '.config'
		if os.path.exists(configPath):
			file = open(dbPath + '.config')
			jsonStr = file.read()
			file.close()
			sceneData = JSONDecoder().decode(jsonStr)
			self.lock.acquire()
			# stop item
			self.stopItem = sceneData.get('stopItem',{})
			# latest layout
			codeItemList = sceneData.get('codeItem',[])
			for uname in codeItemList:
				self.addCodeItem(uname)
			edgeItemList = sceneData.get('edgeItem',[])
			for edgePair in edgeItemList:
				refObj = dbObj.searchRefObj(edgePair[0], edgePair[1])
				if refObj:
					self._doAddCodeEdgeItem(edgePair[0], edgePair[1], refObj)
			if self.itemDict:
				self.selectOneItem(list(self.itemDict.values())[0])
			# scheme
			schemeDict = sceneData.get('scheme',{})
			for name, schemeData in schemeDict.items():
				edgeList = schemeData.get('edge',[])
				newEdgeList = [(edge[0], edge[1]) for edge in edgeList]
				schemeData['edge'] = newEdgeList
			self.scheme = schemeDict
			self.lock.release()
		else:
			print('no such file: ' + dbPath)

	def onCloseDB(self):
		print('close db------------------')
		from db.DBManager import DBManager
		dbPath = DBManager.instance().getDB().getDBPath()
		if not dbPath:
			return
		file = open(dbPath + '.config', 'w')
		codeItemList = list(self.itemDict.keys())
		edgeItemList = list(self.edgeDict.keys())
		jsonDict = {'stopItem':self.stopItem,
					'codeItem':codeItemList,
					'edgeItem':edgeItemList,
					'scheme':self.scheme}
		jsonStr = JSONEncoder().encode(jsonDict)
		file.write(jsonStr)
		file.close()

	def getItemDict(self):
		return self.itemDict

	def isAutoFocus(self):
		return self.autoFocus and self.autoFocusToggle

	def event(self, eventObj):
		#print('CodeScene. event', self, eventObj)
		if getattr(self, 'lock', None):
			self.lock.acquire()
			#print('code scene locked')
			res = super(CodeScene, self).event(eventObj)
			self.lock.release()
			#print('code scene unlocked')

			return res
		#print('super codescene event')
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

	def disconnectSignals(self):
		self.disconnect(self, QtCore.SIGNAL('selectionChanged()'), self, QtCore.SLOT('onSelectItems()'))

	def connectSignals(self):
		self.connect(self, QtCore.SIGNAL('selectionChanged()'), self, QtCore.SLOT('onSelectItems()'))

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
		self.disconnectSignals()
		#print('remove item lru', len(self.itemLruQueue))
		# for idx, itemName in enumerate(self.itemLruQueue):
		# 	print('item:', idx, self.itemDict[self.itemLruQueue[idx]].name)

		queueLength = len(self.itemLruQueue)
		#print ('remove item lru', queueLength, self.lruMaxLength)

		if queueLength > self.lruMaxLength:
			for i in range(self.lruMaxLength, queueLength):
				self._doDeleteCodeItem(self.itemLruQueue[i])

			self.itemLruQueue = self.itemLruQueue[0:self.lruMaxLength]

		# for idx, itemName in enumerate(self.itemLruQueue):
		# 	item = self.itemDict.get(itemName, None)
			# if item:
			# 	opacity = 1.0 - float(idx) / self.lruMaxLength
			# 	item.setOpacity(opacity)
				#print(idx, item, opacity)

		self.connectSignals()

	def getNSelected(self):
		nSelected = 0
		for name, item in self.itemDict.items():
			if item.isSelected():
				nSelected+=1

		for name, item in self.edgeDict.items():
			if item.isSelected():
				nSelected+=1
		return nSelected

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
		if uniqueName in self.stopItem:
			return False, None
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

		#print('do delete code item', node, node.name)
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

		#print('delete list', deleteList)
		for deleteName in deleteList:
			self._doDeleteCodeItem(deleteName)

		self.deleteLRU(deleteList)

		self.itemLruQueue
		self.lock.release()

	def clearOldItem(self):
		if len(self.itemLruQueue) <= 0:
			return

		#print('clear old item ------ begin')
		self.lock.acquire()
		#print('lock ------------------')
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
		#print('delte code item end')
		self.deleteLRU([lastItem])
		#print('delete lru end ')
		self.lock.release()
		#print('clear old item end ----------')

		if lastPos:
			self.selectNearestItem(lastPos)

	def deleteSelectedItems(self, addToStop = True):
		self.lock.acquire()

		#print('acquire lock -----------------------------------------', self.lock)

		itemList = []
		lastPos = None
		for itemKey, item in self.itemDict.items():
			if item.isSelected():
				itemList.append(itemKey)
				lastPos = item.pos()
				if addToStop:
					self.stopItem[item.getUniqueName()] = item.name

		if itemList:
			#print('do delete code item')
			for itemKey in itemList:
				self._doDeleteCodeItem(itemKey)
			#print('delete lru')
			self.deleteLRU(itemList)
			#print('remove item lru')
			self.removeItemLRU()

		if lastPos:
			#print('select nearest item')
			self.selectNearestItem(QtCore.QPointF(lastPos.x(), lastPos.y()))

		#print('before release')
		self.lock.release()
		#print('release lock -----------------------------------------', self.lock)

	def getNode(self, uniqueName):
		node = self.itemDict.get(uniqueName, None)
		return node

	def findNeighbour(self, mainDirection = (1.0,0.0)):
		#print('find neighbour begin', mainDirection)
		itemList = self.selectedItems()
		if not itemList:
			#print('no item', itemList)
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
		#print('find nei', minItem)
		if minItem:
			if self.selectOneItem(minItem):
				#print('show in editor------')
				self.showInEditor()

	def findNeighbourForEdge(self, centerItem, mainDirection):
		from ui.CodeUIItem import CodeUIItem
		from ui.CodeUIEdgeItem import CodeUIEdgeItem

		# 对于函数调用边，先找出其前后的调用
		if centerItem.orderData and math.fabs(mainDirection[1]) > 0.8:
			srcItem = self.itemDict.get(centerItem.srcUniqueName)
			tarItem = self.itemDict.get(centerItem.tarUniqueName)
			if srcItem and tarItem and srcItem.isFunction() and tarItem.isFunction():
				tarOrder = centerItem.orderData[0] - 1 if mainDirection[1] < 0 else centerItem.orderData[0] + 1
				for edgeKey, edge in self.edgeDict.items():
					if edge.srcUniqueName == centerItem.srcUniqueName and edge.orderData and edge.orderData[0] == tarOrder:
						return edge
				return None

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

		if centerItem.isFunction():
			if mainDirection[0] > 0.8:
				for edgeKey, edge in self.edgeDict.items():
					if edge.srcUniqueName == centerItem.getUniqueName() and edge.orderData and edge.orderData[0] == 1:
						return edge

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

		#print('min edge val', minEdgeVal, minEdge)
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

		# 横向优先选边
		if math.fabs(mainDirection[0]) > 0.8:
			if minEdgeConnected:
				return minEdgeConnected
			elif minEdge:
				return minEdge
			elif minNodeConnected:
				return minNodeConnected
			elif minNode:
				return minNode

		# 纵向优先选点
		if math.fabs(mainDirection[1]) > 0.8:
			if minNode:
				return minNode
			elif minNodeConnected:
				return minNodeConnected
			elif minEdgeConnected:
				return minEdgeConnected
			elif minEdge:
				return minEdge

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
		print('select on item')
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
		itemList = self.selectedItems()
		if not itemList:
			return
 
		item = itemList[0]
		if isinstance(item, CodeUIItem):
			entity = item.getEntity()
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
			#print('file ----', line, column, fileName, ref.kind(), ref.kindname())
		elif isinstance(item, CodeUIEdgeItem):
			line = item.line
			column = item.column
			fileName = item.file

		from db.DBManager import DBManager
		socket = DBManager.instance().getSocket()
		socket.remoteCall('goToPage', [fileName, line, column])

	def _addCallPaths(self, srcName, tarName):
		from db.DBManager import DBManager
		from ui.CodeUIItem import CodeUIItem
		dbObj = DBManager.instance().getDB()
		if not dbObj:
			return []

		srcItem = self.itemDict.get(srcName, None)
		tarItem = self.itemDict.get(tarName, None)
		if not srcItem or not tarItem or not isinstance(srcItem, CodeUIItem) or not isinstance(tarItem, CodeUIItem) or\
				not srcItem.isFunction() or not tarItem.isFunction():
			return []

		entList, refList = dbObj.searchCallPaths(srcName, tarName)
		for entName in entList:
			self._doAddCodeItem(entName)
		for refObj in refList:
			self._doAddCodeEdgeItem(refObj[0], refObj[1], refObj[2])
		return entList

	def addCallPaths(self, srcName = '', tarName = ''):
		self.lock.acquire()
		#print('add call path', srcName, tarName)
		if not srcName or not tarName:
			itemList = self.selectedItems()
			srcName, tarName = itemList[0].getUniqueName(), itemList[1].getUniqueName()
			if self.itemLruQueue.index(srcName) < self.itemLruQueue.index(tarName):
				tarName, srcName = srcName, tarName

		entNameList = self._addCallPaths(srcName, tarName)
		self.updateLRU(entNameList)
		self.removeItemLRU()
		self.lock.release()

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
	def testSlot(self):
		print('test')

	@QtCore.pyqtSlot()
	def onSelectItems(self):
		from ui.CodeUIItem import CodeUIItem
		from ui.CodeUIEdgeItem import CodeUIEdgeItem
		itemList = self.selectedItems()
		#print( 'on select items begin', itemList)

		for item in itemList:
			if not isinstance(item, CodeUIItem):
				continue
			uniqueName = item.getUniqueName()
			self.updateLRU([uniqueName])

		self.removeItemLRU()
		#print( 'on select items end', itemList)
