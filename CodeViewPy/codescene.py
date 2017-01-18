# -*- coding: utf-8 -*-
import sys
import os
from PyQt4 import QtCore, QtGui, uic, Qt
import math
import random
import time
import hashlib
from json import *

class SceneUpdateThread(QtCore.QThread):
	updateSignal = QtCore.pyqtSignal()
	def __init__(self, scene, lock):
		super(SceneUpdateThread, self).__init__()
		self.scene = scene
		self.lock = lock
		self.isActive = True
		self.itemSet = set()
		self.edgeNum = 0
		print(self.updateSignal)
		self.updateSignal.connect(self.scene.update, Qt.Qt.QueuedConnection)
		self.sleepTime = 300

	def setActive(self, isActive):
		self.lock.acquire()
		self.isActive = isActive
		self.lock.release()

	def run(self):
		t0 = 0
		while True:
			begTime = time.time()
			if self.isActive:
				#print('interval', time.time() - t0)
				t0 = time.time() * 1000
				self.scene.acquireLock()
				if self.itemSet != set(self.scene.itemDict.keys()) or self.edgeNum != len(self.scene.edgeDict) or self.scene.isLayoutDirty:
					self.updateLayeredLayoutWithComp()
					self.scene.isLayoutDirty = False
				t1 = time.time() * 1000
				self.moveItems()
				t2 = time.time() * 1000
				self.updateCallOrder()
				t3 = time.time() * 1000
				self.scene.updateCurrentValidScheme()
				t4 = time.time() * 1000
				self.scene.updateCandidateEdge()
				t5 = time.time() * 1000
				self.updateSignal.emit()
				t6 = time.time() * 1000
				self.scene.releaseLock()
				# print('time %.0f %.0f %.0f %.0f %.0f %.0f' % (t1-t0,t2-t1,t3-t2,t4-t3,t5-t4,t6-t5))

			duration = time.time() - begTime
			remainTime = self.sleepTime - duration * 1000
			# print('remain time: %.0f' % remainTime)
			if remainTime > 0:
				self.msleep(remainTime)

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
			posList[i] = posI - offset
			posList[j] = posJ + offset

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
				self.height = max(radius, height)
				self.firstKey = 0.0
				self.secondKey = 0.0
				self.thirdKey = 0.0

			def getLayoutHeight(self):
				return self.height + self.radius

			def setLayoutPos(self,x,y):
				self.pos = (x, y-0.5*(self.height - self.radius))

			def getMinX(self):
				return self.pos[0] - self.radius

			def getMaxX(self):
				return self.pos[0] + self.radius

			def getMinY(self):
				return self.pos[1] - self.radius

			def getMaxY(self):
				return self.pos[1] + self.height

			def getPos(self):
				return self.pos

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
			v1 = vtxName2Id[edgeKey[0]]
			v2 = vtxName2Id[edgeKey[1]]
			vtxList[v1].outNodes.add(v2)
			vtxList[v2].inNodes.add(v1)
			edgeList.append((v1,v2))

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

			# 增加一个连通分量
			compList.append(compMap)

		from grandalf.graphs import Vertex, Edge, Graph
		class VtxView(object):
			def __init__(self, w, h):
				self.w = w
				self.h = h

		# 构造每个连通分量的图结构
		offset = (0,0)
		bboxMin = [1e6,1e6]
		bboxMax = [-1e6,-1e6]
		self.scene.boxTest = []
		for ithComp, compMap in enumerate(compList):
			minPnt = [1e6,1e6]
			maxPnt = [-1e6,-1e6]

			# 构造图数据并布局
			V = []
			for oldId in compMap:
				w = vtxList[oldId].getLayoutHeight()
				vtx = Vertex(oldId)
				height = 200
				vtx.view = VtxView(w, height)
				V.append(vtx)

			E = []
			for edgeKey in edgeList:
				if vtxList[edgeKey[0]].comp == ithComp:
					E.append(Edge(V[vtxList[edgeKey[0]].compIdx], V[vtxList[edgeKey[1]].compIdx]))

			g = Graph(V,E)
			from grandalf.layouts import SugiyamaLayout
			packSpace = 4
			sug = SugiyamaLayout(g.C[0])
			sug.xspace = packSpace
			sug.yspace = packSpace
			#sug.order_iter = 32
			sug.dirvh = 3
			sug.init_all()
			sug.draw(10)

			# 统计包围盒
			for v in g.C[0].sV:
				oldV = vtxList[v.data]
				x= v.view.xy[1]
				y= v.view.xy[0]
				oldV.setLayoutPos(x,y)

				minPnt[0] = min(minPnt[0],oldV.getMinX())
				minPnt[1] = min(minPnt[1],oldV.getMinY())
				maxPnt[0] = max(maxPnt[0],oldV.getMaxX())
				maxPnt[1] = max(maxPnt[1],oldV.getMaxY())

			for v in g.C[0].sV:
				oldV = vtxList[v.data]
				posInComp = oldV.getPos()
				newPos = (posInComp[0], posInComp[1]-minPnt[1]+offset[1])
				self.scene.itemDict[oldV.name].setTargetPos(QtCore.QPointF(newPos[0], newPos[1]))
				bboxMin[0] = min(bboxMin[0], newPos[0])
				bboxMin[1] = min(bboxMin[1], newPos[1])
				bboxMax[0] = max(bboxMax[0], newPos[0])
				bboxMax[1] = max(bboxMax[1], newPos[1])

			offset = (offset[0], offset[1]+maxPnt[1]-minPnt[1]+packSpace)

		# 设置四个角的item
		cornerList = self.scene.cornerItem
		mar = 2000
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
			edge.isConnectedToFocusNode = False
		for key, node in self.scene.itemDict.items():
			node.isConnectedToFocusNode = False

		item = self.scene.selectedItems()
		if not item:
			return
		item = item[0]
		self.updateCallOrderByItem(item)

		if isinstance(item, ui.CodeUIItem.CodeUIItem) and item.isFunction():
			caller = []
			for key, edge in self.scene.edgeDict.items():
				if key[1] == item.getUniqueName() and self.scene.itemDict[key[0]].isFunction():
					caller.append(self.scene.itemDict[key[0]])
			if len(caller) == 1:
				self.updateCallOrderByItem(caller[0])

	def updateCallOrderByItem(self, item):
		import ui.CodeUIItem
		import ui.CodeUIEdgeItem
		isEdgeSelected = False
		if isinstance(item, ui.CodeUIEdgeItem.CodeUIEdgeItem):
			srcItem = self.scene.itemDict.get(item.srcUniqueName, None)
			dstItem = self.scene.itemDict.get(item.tarUniqueName, None)
			isEdgeSelected = True
			if srcItem and dstItem:
				srcItem.isConnectedToFocusNode = dstItem.isConnectedToFocusNode = True
			item = srcItem
		if not item or item.kind != ui.CodeUIItem.ITEM_FUNCTION:
			return

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

		edgeList.sort(key = lambda edge: edge.line - edge.column / 1000.0)

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
				x = basePos + padding# + stepSize * int((nEdge-i-1) / levelSize)
				y = edge.findCurveYPos(x)
				edge.orderData = (i+1, QtCore.QPointF(x,y))

	def moveItems(self):
		pos = QtCore.QPointF(0,0)
		nSelected = 0
		bboxMin = [1e6, 1e6]
		bboxMax = [-1e6, -1e6]
		maxDisp = 0
		moveRatio = 0.07
		for name, item in self.scene.itemDict.items():
			disp = item.dispToTarget()
			maxDisp = max(maxDisp, disp.manhattanLength() * moveRatio)
			item.moveToTarget(moveRatio)
			if item.isSelected():
				pos += item.pos()
				nSelected+=1
			newPos = item.pos()
			bboxMin[0] = min(bboxMin[0], newPos.x())
			bboxMin[1] = min(bboxMin[1], newPos.y())
			bboxMax[0] = max(bboxMax[0], newPos.x())
			bboxMax[1] = max(bboxMax[1], newPos.y())

		for name, item in self.scene.edgeDict.items():
			item.buildPath()
			if item.isSelected():
				pos += item.getMiddlePos()
				nSelected+=1

		# 设置四个角的item
		if bboxMax[0] > bboxMin[0] and bboxMax[1] > bboxMin[1]:
			cornerList = self.scene.cornerItem
			mar = 2000
			cornerList[0].setPos(bboxMin[0]-mar, bboxMin[1]-mar)
			cornerList[1].setPos(bboxMin[0]-mar, bboxMax[1]+mar)
			cornerList[2].setPos(bboxMax[0]+mar, bboxMin[1]-mar)
			cornerList[3].setPos(bboxMax[0]+mar, bboxMax[1]+mar)

		for view in self.scene.views():
			if self.scene.isAutoFocus() and self.scene.getNSelected() > 0:
				mousePos = view.mapFromGlobal(QtGui.QCursor.pos())
				isInView = view.rect().contains(mousePos)
				if isInView:
					view.centerPnt = view.mapToScene(view.rect().center())
					continue
				pos = self.scene.getSelectedCenter()
				if getattr(view, 'centerPnt', None) is not None:
					disp = view.centerPnt - pos
					maxDisp = max(maxDisp, disp.manhattanLength() * moveRatio)
					view.centerPnt = view.centerPnt * (1.0 - moveRatio) + pos * moveRatio
				view.centerOn(view.centerPnt)
			else:
				view.centerPnt = view.mapToScene(view.rect().center())

		if maxDisp > 0.1:
			self.sleepTime = 30
		else:
			self.sleepTime = 300

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
		self.scheme = {}		# 保存的call graph,
								# {'schemeName': {'node':[node1, node2,...], 'edge':{(node3, node5):{'customEdge':True}, ...}}, ...}
		self.curValidScheme = []# 选中物体有关的scheme
		self.curValidSchemeColor = []
		self.candidateEdge = [] # candidate edge up/down/left/right will select
		self.isSourceCandidate = True
		self.edgeDataDict = {}  # 存放需要保存的边用户数据
		self.itemDataDict = {}	# 存放需要保存的点用户数据

		self.itemLruQueue = []
		self.lruMaxLength = 100
		self.isLayoutDirty = False

		self.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
		self.lock = RecursiveLock()
		self.updateThread = SceneUpdateThread(self, self.lock)
		self.updateThread.start()

		self.cornerItem = []
		self.autoFocus = True
		self.autoFocusToggle = True
		self.selectTimeStamp = 0
		for i in range(4):
			item = QtGui.QGraphicsRectItem(0,0,5,5)
			item.setPen(QtGui.QPen(QtGui.QColor(0,0,0,0)))
			item.setBrush(QtGui.QBrush())
			self.cornerItem.append(item)
			self.addItem(item)
		self.connect(self, QtCore.SIGNAL('selectionChanged()'), self, QtCore.SLOT('onSelectItems()'))

	# 添加或修改call graph
	def addOrReplaceIthScheme(self, ithScheme):
		if ithScheme < 0 or ithScheme >= len(self.curValidScheme):
			return
		name = self.curValidScheme[ithScheme]
		self.addOrReplaceScheme(name)
		self.showScheme(name, True)

	def toggleSelectedEdgeToScheme(self, ithScheme):
		if ithScheme < 0 or ithScheme >= len(self.curValidScheme):
			return
		self.acquireLock()
		name = self.curValidScheme[ithScheme]
		schemeNodeSet = set(self.scheme[name]['node'])
		schemeEdgeDict = self.scheme[name]['edge']

		newItems = set()
		newEdges = set()
		for edgeName, edge in self.edgeDict.items():
			if edge.isSelected():
				isAdd = True
				if edgeName in schemeEdgeDict:
					isAdd = False

				if isAdd:
					schemeEdgeDict[edgeName] = {}
					schemeNodeSet.add(edge.srcUniqueName)
					schemeNodeSet.add(edge.tarUniqueName)
				else:
					del schemeEdgeDict[edgeName]
					isSrcNodeDelete = edge.srcUniqueName in schemeNodeSet
					isTarNodeDelete = edge.tarUniqueName in schemeNodeSet
					for edgePair, edgeData in schemeEdgeDict.items():
						if edge.srcUniqueName in edgePair:
							isSrcNodeDelete = False
						if edge.tarUniqueName in edgePair:
							isTarNodeDelete = False
					if isSrcNodeDelete:
						schemeNodeSet.remove(edge.srcUniqueName)
					if isTarNodeDelete:
						schemeNodeSet.remove(edge.tarUniqueName)

		self.scheme[name] = {'node': list(schemeNodeSet), 'edge':schemeEdgeDict}
		self.releaseLock()

	def addOrReplaceScheme(self, name):
		print('add or replace scheme', name)
		nodes = [uname for uname, item in self.itemDict.items() if item.isSelected()]
		if not nodes:
			return
		def bothNodesSelected(edge):
			srcItem = self.itemDict.get(edge.srcUniqueName)
			tarItem = self.itemDict.get(edge.tarUniqueName)
			if not srcItem or not tarItem:
				return False
			return srcItem.isSelected() and tarItem.isSelected()

		edges = {}
		for edgePair, item in self.edgeDict.items():
			if bothNodesSelected(item):
				edgeData = {}
				edges[edgePair] = edgeData
		self.scheme[name] = {'node': nodes, 'edge':edges}

	def getSchemeNameList(self):
		return [name for name, schemeData in self.scheme.items()]

	def deleteScheme(self, name):
		if name in self.scheme:
			del self.scheme[name]

	def showScheme(self, name, selectScheme = True):
		if name not in self.scheme:
			return False

		self.acquireLock()
		selectedNode = []
		selectedEdge = []
		if not selectScheme:
			for uname, node in self.itemDict.items():
				if node.isSelected():
					selectedNode.append(uname)
			for uname, edge in self.edgeDict.items():
				if edge.isSelected():
					selectedEdge.append(uname)

		from db.DBManager import DBManager
		dbObj = DBManager.instance().getDB()
		codeItemList = self.scheme[name].get('node',[])
		for uname in codeItemList:
			res, item = self.addCodeItem(uname)

		self.clearSelection()
		for uname in codeItemList:
			item = self.itemDict.get(uname)
			if item and selectScheme:
				item.setSelected(True)

		edgeItemDict = self.scheme[name].get('edge',{})
		for edgePair, _ in edgeItemDict.items():
			# 自定义边一定能够创建
			edgeData = self.edgeDataDict.get(edgePair, {})
			if edgeData.get('customEdge', False):
				self._doAddCodeEdgeItem(edgePair[0], edgePair[1], {'customEdge':True})
			else:
				refObj = dbObj.searchRefObj(edgePair[0], edgePair[1])
				if refObj:
					self._doAddCodeEdgeItem(edgePair[0], edgePair[1], {'dbRef':refObj})
			edgeItem = self.edgeDict.get(edgePair)
			if edgeItem and selectScheme:
				edgeItem.setSelected(True)

		if not selectScheme:
			for uname in selectedNode:
				node = self.itemDict.get(uname)
				if node:
					node.setSelected(True)
			for uname in selectedEdge:
				edge = self.edgeDict.get(uname)
				if edge:
					edge.setSelected(True)

		self.releaseLock()

	def showIthScheme(self, ithScheme, isSelected = False):
		if ithScheme < 0 or ithScheme >= len(self.curValidScheme):
			return
		name = self.curValidScheme[ithScheme]
		self.showScheme(name, isSelected)

	def getCurrentSchemeList(self):
		return self.curValidScheme

	def getCurrentSchemeColorList(self):
		return self.curValidSchemeColor

	def updateCurrentValidScheme(self):
		schemeNameSet = set()

		edgeSet = set()
		nodeSet = set()
		for uname, item in self.edgeDict.items():
			item.schemeColorList = []
			if item.isSelected():
				edgeSet.add(uname)
				nodeSet.add(item.srcUniqueName)
				nodeSet.add(item.tarUniqueName)
			elif self.itemDict[item.srcUniqueName].isSelected():
				edgeSet.add(uname)
				nodeSet.add(item.srcUniqueName)
			elif self.itemDict[item.tarUniqueName].isSelected():
				edgeSet.add(uname)
				nodeSet.add(item.tarUniqueName)

		for uname in nodeSet:
			for schemeName, schemeData in self.scheme.items():
				if uname in schemeData['node']:
					schemeNameSet.add(schemeName)

		for uname in edgeSet:
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
			return QtGui.QColor.fromHslF(h, 0.6+s*0.3, 0.3+l*0.2)

		for schemeName in self.curValidScheme:
			schemeData = self.scheme[schemeName]
			schemeColor = schemeName2color(schemeName)
			self.curValidSchemeColor.append(schemeColor)
			for edgePair, edgeData in schemeData['edge'].items():
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
		jsonStr = ''
		if os.path.exists(configPath):
			file = open(dbPath + '.config')
			jsonStr = file.read()
			file.close()
		if jsonStr:
			sceneData = JSONDecoder().decode(jsonStr)
			self.lock.acquire()
			# stop item
			self.stopItem = sceneData.get('stopItem',{})
			self.itemDataDict = sceneData.get('codeData',{})
			# latest layout
			codeItemList = sceneData.get('codeItem',[])
			for uname in codeItemList:
				self.addCodeItem(uname)

			for edgeData in sceneData.get('edgeData', []):
				self.edgeDataDict[(edgeData[0], edgeData[1])] = edgeData[2]

			edgeItemList = sceneData.get('edgeItem',[])
			for edgePair in edgeItemList:
				if self.edgeDataDict.get((edgePair[0], edgePair[1]), {}).get('customEdge', False):
					self._doAddCodeEdgeItem(edgePair[0], edgePair[1], {'customEdge':True})
				else:
					refObj = dbObj.searchRefObj(edgePair[0], edgePair[1])
					if refObj:
						self._doAddCodeEdgeItem(edgePair[0], edgePair[1], {'dbRef':refObj})
			if self.itemDict:
				self.selectOneItem(list(self.itemDict.values())[0])
			# scheme
			schemeDict = sceneData.get('scheme',{})
			for name, schemeData in schemeDict.items():
				edgeList = schemeData.get('edge',[])
				edgeDict = {}
				for edgeData in edgeList:
					edgeDict[(edgeData[0], edgeData[1])] = {}
				schemeData['edge'] = edgeDict
			self.scheme = schemeDict
			self.lock.release()
		else:
			print('no config file: ' + configPath)

	def onCloseDB(self):
		print('close db------------------')
		from db.DBManager import DBManager
		dbPath = DBManager.instance().getDB().getDBPath()
		if not dbPath:
			return
		file = open(dbPath + '.config', 'w')
		codeItemList = list(self.itemDict.keys())
		edgeItemList = list(self.edgeDict.keys())
		edgeDataList = []
		for edgeKey, edgeData in self.edgeDataDict.items():
			edgeDataList.append([edgeKey[0], edgeKey[1], edgeData])

		# 修改scheme边的数据格式，以便存成json格式
		import copy
		scheme = copy.deepcopy(self.scheme)
		for schemeName, schemeData in scheme.items():
			edgeList = []
			for edgeKey, edgeData in schemeData.get('edge',{}).items():
				edgeList.append([edgeKey[0], edgeKey[1]])
			schemeData['edge'] = edgeList
		jsonDict = {'stopItem':self.stopItem,
					'codeItem':codeItemList,
					'codeData':self.itemDataDict,
					'edgeItem':edgeItemList,
					'edgeData':edgeDataList,
					'scheme':scheme}
		jsonStr = JSONEncoder().encode(jsonDict)
		file.write(jsonStr)
		file.close()

	def getItemDict(self):
		return self.itemDict

	def isAutoFocus(self):
		return self.autoFocus and self.autoFocusToggle

	def event(self, eventObj):
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
			else:
				# 已有的项
				del self.itemLruQueue[idx]

			self.itemLruQueue.insert(0, itemKey)
		return []#deleteKeyList

	def removeItemLRU(self):
		self.disconnectSignals()

		queueLength = len(self.itemLruQueue)

		if queueLength > self.lruMaxLength:
			for i in range(self.lruMaxLength, queueLength):
				self._doDeleteCodeItem(self.itemLruQueue[i])

			self.itemLruQueue = self.itemLruQueue[0:self.lruMaxLength]


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
		item.setPos(self.getSelectedCenter())
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

	def addSimilarCodeItem(self):
		itemList = self.selectedItems()
		if not itemList:
			return
		item = itemList[0]

		from ui.CodeUIItem import CodeUIItem
		from ui.CodeUIEdgeItem import CodeUIEdgeItem
		from db.DBManager import DBManager

		if not isinstance(item, CodeUIItem):
			return

		db = DBManager.instance().getDB()
		name = item.name
		uname = item.getUniqueName()
		if not db or not name or not item.isFunction():
			return
		ents = db.search(name, 'function')

		bestEntList = []
		if not ents:
			return
		for ent in ents:
			if ent and ent.name() == name:
				bestEntList.append(ent)

		for ent in bestEntList:
			entUname = ent.uniquename()
			res, entItem = self.addCodeItem(entUname)
			if self.edgeDict.get((uname, entUname)) or self.edgeDict.get((entUname, uname)):
				continue
			if uname == entUname:
				continue
			if not entItem.customData.get('hasDef'):
				self.addCustomEdge(entUname, uname)
			else:
				self.addCustomEdge(uname, entUname)

	def _doAddCodeEdgeItem(self, srcUniqueName, tarUniqueName, dataObj):
		key = (srcUniqueName, tarUniqueName)
		if self.edgeDict.get(key, None):
			return False
		if srcUniqueName not in self.itemDict or tarUniqueName not in self.itemDict:
			return False

		from ui.CodeUIEdgeItem import CodeUIEdgeItem
		item = CodeUIEdgeItem(srcUniqueName, tarUniqueName, edgeData = dataObj)
		self.edgeDict[key] = item
		if dataObj.get('customEdge', False):
			edgeData = self.edgeDataDict.get(key, {})
			edgeData['customEdge'] = True
			self.edgeDataDict[key] = edgeData
		self.addItem(item)
		return True

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

		for deleteName in deleteList:
			self._doDeleteCodeItem(deleteName)

		self.deleteLRU(deleteList)

		self.lock.release()

	def clearOldItem(self):
		if len(self.itemLruQueue) <= 0:
			return

		self.lock.acquire()

		lastItem = self.itemLruQueue[-1]
		lastPos = self.itemDict[lastItem].pos()
		self._doDeleteCodeItem(lastItem)
		self.deleteLRU([lastItem])
		self.lock.release()

		if lastPos:
			self.selectNearestItem(lastPos)

	def deleteNearbyItems(self):
		minScoreList =[]
		for edgeKey, edge in self.edgeDict.items():
			srcItem = self.itemDict.get(edgeKey[0])
			tarItem = self.itemDict.get(edgeKey[1])
			if not srcItem or not tarItem or srcItem.isSelected() == tarItem.isSelected():
				continue
			if srcItem.isSelected():
				minScoreList.append((tarItem.selectCounter, tarItem.getUniqueName()))
			else:
				minScoreList.append((srcItem.selectCounter, srcItem.getUniqueName()))

		if not minScoreList:
			return

		minScoreList.sort(key = lambda item: item[0])
		deleteList = []
		deleteScore = minScoreList[0][0]
		for item in minScoreList:
			if item[0] == deleteScore:
				deleteList.append(item[1])

		self.lock.acquire()

		for deleteName in deleteList:
			self._doDeleteCodeItem(deleteName)

		self.deleteLRU(deleteList)

		self.lock.release()

	def deleteSelectedItems(self, addToStop = True):
		self.lock.acquire()

		itemList = []
		lastPos = None
		for itemKey, item in self.itemDict.items():
			if item.isSelected():
				itemList.append(itemKey)
				lastPos = item.pos()
				if addToStop:
					self.stopItem[item.getUniqueName()] = item.name

		for edgeKey, edge in self.edgeDict.items():
			if edge.isSelected():
				srcItem = self.itemDict[edgeKey[0]]
				lastPos = srcItem.pos()
				break

		lastFunction = None
		if len(itemList) == 1 and self.itemDict[itemList[0]].isFunction():
			funItem = self.itemDict[itemList[0]]
			callEdgeKey = None
			callEdge = None
			order = None
			for edgeKey, edge in self.edgeDict.items():
				if edgeKey[1] == funItem.getUniqueName():
					callEdgeKey = edgeKey
					callEdge = edge
					order = callEdge.getCallOrder()
					break

			if callEdgeKey and callEdge and order:
				for edgeKey, edge in self.edgeDict.items():
					if edgeKey[0] == callEdgeKey[0] and edge.getCallOrder() == order+1:
						lastFunction = edge
						break

		if itemList:
			for itemKey in itemList:
				self._doDeleteCodeItem(itemKey)
			self.deleteLRU(itemList)
			self.removeItemLRU()

		edgeList = []
		for itemKey, item in self.edgeDict.items():
			if item.isSelected():
				edgeList.append(itemKey)
		for edgeKey in edgeList:
			self._doDeleteCodeEdgeItem(edgeKey)

		res = None
		if lastFunction:
			res = self.selectOneItem(lastFunction)
		elif lastPos:
			res = self.selectNearestItem(QtCore.QPointF(lastPos.x(), lastPos.y()))

		if res:
			self.showInEditor()
		self.lock.release()

	def getNode(self, uniqueName):
		node = self.itemDict.get(uniqueName, None)
		return node

	def findNeighbour(self, mainDirection = (1.0,0.0)):
		itemList = self.selectedItems()
		if not itemList:
			return

		from ui.CodeUIItem import CodeUIItem
		from ui.CodeUIEdgeItem import CodeUIEdgeItem
		centerItem = itemList[0]
		centerIsNode = isinstance(centerItem, CodeUIItem)
		if centerIsNode:
			minItem = self.findNeighbourForNode(centerItem, mainDirection)
		else:
			minItem = self.findNeighbourForEdge(centerItem, mainDirection)

		if minItem:
			if self.selectOneItem(minItem):
				self.showInEditor()

	def updateCandidateEdge(self):
		from ui.CodeUIItem import CodeUIItem
		from ui.CodeUIEdgeItem import CodeUIEdgeItem

		centerItem = None
		for edgeKey, edge in self.edgeDict.items():
			edge.isCandidate = False
			if edge.isSelected():
				centerItem = edge

		if not centerItem:
			return

		# find edge set
		self.candidateEdge = []
		srcEdgeList = []
		tarEdgeList = []
		srcNode = self.getNode(centerItem.srcUniqueName)
		tarNode = self.getNode(centerItem.tarUniqueName)
		for edgeKey, edge in self.edgeDict.items():
			if edge == centerItem:
				continue
			if edgeKey[0] == centerItem.srcUniqueName:
				srcEdgeList.append(edgeKey)
			elif edgeKey[1] == centerItem.tarUniqueName and edgeKey[0] != centerItem.tarUniqueName:
				tarEdgeList.append(edgeKey)

		self.isSourceCandidate = True
		if len(tarEdgeList) == 0 and len(srcEdgeList) > 0:
			self.candidateEdge = srcEdgeList
		elif len(srcEdgeList) == 0 and len(tarEdgeList) > 0:
			self.candidateEdge = tarEdgeList
			self.isSourceCandidate = False
		elif tarNode.selectTimeStamp > srcNode.selectTimeStamp:
			self.candidateEdge = tarEdgeList
			self.isSourceCandidate = False
		else:
			self.candidateEdge = srcEdgeList

		for edgeKey in self.candidateEdge:
			edge = self.edgeDict.get(edgeKey)
			if edge:
				edge.isCandidate = True

	def findNeighbourForEdge(self, centerItem, mainDirection):
		from ui.CodeUIItem import CodeUIItem
		from ui.CodeUIEdgeItem import CodeUIEdgeItem

		# 对于函数调用边，先找出其前后的调用
		if self.isSourceCandidate and centerItem.orderData and math.fabs(mainDirection[1]) > 0.8:
			srcItem = self.itemDict.get(centerItem.srcUniqueName)
			tarItem = self.itemDict.get(centerItem.tarUniqueName)
			if srcItem and tarItem and srcItem.isFunction() and tarItem.isFunction():
				tarOrder = centerItem.orderData[0] - 1 if mainDirection[1] < 0 else centerItem.orderData[0] + 1
				for edgeKey in self.candidateEdge:
					edge = self.edgeDict.get(edgeKey)
					if edge and edge.srcUniqueName == centerItem.srcUniqueName and edge.orderData and edge.orderData[0] == tarOrder:
						return edge
			return None

		srcNode = self.getNode(centerItem.srcUniqueName)
		tarNode = self.getNode(centerItem.tarUniqueName)
		nCommonIn = 0
		nCommonOut= 0
		for edgeKey in self.candidateEdge:
			if edgeKey[0] == centerItem.srcUniqueName:
				nCommonIn += 1
			if edgeKey[1] == centerItem.tarUniqueName:
				nCommonOut += 1

		percent = 0.5
		if self.isSourceCandidate:
			percent = 0.2
		else:
			percent = 0.8
		centerPos = centerItem.pointAtPercent(percent)

		srcPos, tarPos = centerItem.getNodePos()
		edgeDir = tarPos - srcPos
		edgeDir /= math.sqrt(edgeDir.x()*edgeDir.x() + edgeDir.y()*edgeDir.y() + 1e-5)
		proj = mainDirection[0]*edgeDir.x() + mainDirection[1]*edgeDir.y()
 
		if math.fabs(mainDirection[0]) > 0.8:
			if proj > 0.0 and tarNode:
				return tarNode
			elif proj < 0.0 and srcNode:
				return srcNode

		# 找出最近的边
		minEdgeVal = 1.0e12
		minEdge = None
		centerKey = (centerItem.srcUniqueName, centerItem.tarUniqueName)
		for edgeKey in self.candidateEdge:
			item = self.edgeDict.get(edgeKey)
			if not item:
				continue
			if item is centerItem:
				continue
			if not (edgeKey[0] in centerKey or edgeKey[1] in centerKey):
				continue
			y = item.findCurveYPos(centerPos.x())
			dPos = QtCore.QPointF(centerPos.x(), y) - centerPos
			cosVal = (dPos.x() * mainDirection[0] + dPos.y() * mainDirection[1]) / \
					 math.sqrt(dPos.x()*dPos.x() + dPos.y()*dPos.y()+1e-5)
			if cosVal < 0.0:
				continue
			xProj = dPos.x()*mainDirection[0] + dPos.y()*mainDirection[1]
			yProj = dPos.x()*mainDirection[1] - dPos.y()*mainDirection[0]

			xProj /= 2.0
			dist = xProj * xProj + yProj * yProj
			if dist < minEdgeVal:
				minEdgeVal = dist
				minEdge = item

		if minEdge:
			return minEdge

		# 找出最近的节点
		minNodeValConnected = 1.0e12
		minNodeConnected = None
		minNodeVal = 1.0e12
		minNode = None
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
			if not refs:
				refs = entity.refs('declarein')
			if not refs:
				refs = entity.refs('callby')
			if not refs:
				refs = entity.refs('useby')
			if not refs:
				return

			ref = refs[0]
			fileEnt = ref.file()
			line = ref.line()
			column = ref.column()
			fileName = fileEnt.longname()
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
			self._doAddCodeEdgeItem(refObj[0], refObj[1], {'dbRef':refObj[2]})
		return entList

	def addCustomEdge(self, srcName, tarName, edgeData = {}):
		if srcName not in self.itemDict or tarName not in self.itemDict:
			return
		self.acquireLock()
		edgeData['customEdge'] = True
		res = self._doAddCodeEdgeItem(srcName, tarName, edgeData)
		self.releaseLock()

	def addCallPaths(self, srcName = '', tarName = ''):
		self.lock.acquire()
		if not srcName or not tarName:
			itemList = self.selectedItems()
			srcName, tarName = itemList[0].getUniqueName(), itemList[1].getUniqueName()
			if self.itemLruQueue.index(srcName) < self.itemLruQueue.index(tarName):
				tarName, srcName = srcName, tarName

		entNameList = self._addCallPaths(srcName, tarName)
		self.updateLRU(entNameList)
		self.removeItemLRU()
		self.lock.release()

	def _addRefs(self, refStr, entStr, inverseEdge = False, maxCount = -1):
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

			# add to candidate
			candidateList = []
			for ithEnt, entName in enumerate(entNameList):
				refObj = refList[ithEnt]
				entObj = refObj.ent()
				# get lines
				metricRes = entObj.metric(('CountLine',))
				metricLine = metricRes.get('CountLine',1)
				line = metricLine if metricLine else 0
				candidateList.append([entName, refObj, line])

			# sort candidate
			if maxCount > 0:
				candidateList.sort(key = lambda element: element[2], reverse=True)

			addedList = []
			for ithRef, candidate in enumerate(candidateList):
				entName = candidate[0]
				refObj  = candidate[1]
				res, refItem = scene._doAddCodeItem(entName)

				if res:
					addedList.append(entName)
				if inverseEdge:
					scene._doAddCodeEdgeItem(uniqueName, entName, {'dbRef':refObj})
				else:
					scene._doAddCodeEdgeItem(entName, uniqueName, {'dbRef':refObj})

				if len(addedList) >= maxCount > 0:
					break
			refNameList += addedList

		return refNameList


	def addRefs(self, refStr, entStr, inverseEdge = False, maxCount = -1):
		self.lock.acquire()
		refNameList = self._addRefs(refStr, entStr, inverseEdge, maxCount)
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

		i=0
		for itemName, item in self.itemDict.items():
			item.setPos(posList[i])
			i += 1


	@QtCore.pyqtSlot()
	def testSlot(self):
		print('test')

	@QtCore.pyqtSlot()
	def onSelectItems(self):
		from ui.CodeUIItem import CodeUIItem
		from ui.CodeUIEdgeItem import CodeUIEdgeItem
		itemList = self.selectedItems()
		# update LRU
		self.selectTimeStamp += 1
		for item in itemList:
			if not isinstance(item, CodeUIItem):
				continue
			item.selectCounter += 1
			item.selectTimeStamp = self.selectTimeStamp
			uniqueName = item.getUniqueName()
			self.updateLRU([uniqueName])

		self.removeItemLRU()

		# update comment
		itemName = ''
		itemComment = ''
		if len(itemList) == 1:
			item = itemList[0]
			if isinstance(item, CodeUIItem):
				itemName = item.name
				itemComment = self.itemDataDict.get(item.uniqueName, {}).get('comment','')
			elif isinstance(item, CodeUIEdgeItem):
				srcItem = self.itemDict.get(item.srcUniqueName)
				tarItem = self.itemDict.get(item.tarUniqueName)
				if srcItem and tarItem:
					itemName = srcItem.name + ' -> ' + tarItem.name
					itemComment = self.edgeDataDict.get((item.srcUniqueName, item.tarUniqueName), {}).get('comment', '')

		from UIManager import UIManager
		symbolWidget = UIManager.instance().getMainUI().getSymbolWidget()
		if symbolWidget:
			symbolWidget.updateSymbol(itemName, itemComment)

	def updateSelectedComment(self, comment):
		itemList = self.selectedItems()
		from ui.CodeUIItem import CodeUIItem
		from ui.CodeUIEdgeItem import CodeUIEdgeItem

		self.acquireLock()
		if len(itemList) == 1:
			item = itemList[0]
			if isinstance(item, CodeUIItem):
				itemData = self.itemDataDict.get(item.uniqueName, {})
				itemData['comment'] = comment
				self.itemDataDict[item.uniqueName] = itemData
				item.buildCommentSize(comment)
			elif isinstance(item, CodeUIEdgeItem):
				srcItem = self.itemDict.get(item.srcUniqueName)
				tarItem = self.itemDict.get(item.tarUniqueName)
				if srcItem and tarItem:
					edgeData = self.edgeDataDict.get((item.srcUniqueName, item.tarUniqueName), {})
					edgeData['comment'] = comment
					self.edgeDataDict[(item.srcUniqueName, item.tarUniqueName)] = edgeData

			self.isLayoutDirty = True

		self.releaseLock()
