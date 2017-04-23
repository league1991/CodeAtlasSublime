# -*- coding: utf-8 -*-
import sys
import os
from PyQt4 import QtCore, QtGui, Qt
import understand
import subprocess
from db.SymbolNode import FileData, SymbolNode

class CodeDB(QtCore.QObject):
	reopenSignal = QtCore.pyqtSignal()
	def __init__(self):
		super(CodeDB, self).__init__()
		self._db = None
		self._dbPath = ''
		self.reopenSignal.connect(self.reopen, Qt.Qt.QueuedConnection)

	def open(self, path):
		if self._db:
			self._db.close()
		self._dbPath = path
		self._db = understand.open(path)
		self.onOpen()

	def getDBPath(self):
		return self._dbPath

	def close(self):
		if self._db:
			self._db.close()

	@QtCore.pyqtSlot()
	def reopen(self):
		if self._dbPath:
			self._db = understand.open(self._dbPath)
			self.onOpen()

	def analyze(self):
		if self._db and self._dbPath:
			self._db.close()
			self._db = None

			cmdStr = r'und analyze "%s"' % self._dbPath
			workingPath = r'D:\Program Files (x86)\SciTools\bin\pc-win32'

			#os.system(cmdStr)
			p = subprocess.call(cmdStr, timeout= None, cwd = workingPath)
			#p.wait()

			print ('wait finish--------------------', self._dbPath)
			self.reopenSignal.emit()
			print('open finish')

	def onOpen(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		scene.onOpenDB()

		mainUI = UIManager.instance().getMainUI()
		mainUI.symbolDock.widget().updateForbiddenSymbol()
		mainUI.schemeDock.widget().updateScheme()

	def search(self, name, kindstring = None):
		if not self._db:
			return []
		res = self._db.lookup(name, kindstring)
		return res

	def searchFromUniqueName(self, uniqueName):
		if not self._db:
			return None
		return self._db.lookup_uniquename(uniqueName)

	def searchRefEntity(self, uniqueName, refKindStr, entKindStr, isUnique = True):
		if not self._db:
			return [],[]
		ent = self._db.lookup_uniquename(uniqueName)
		if not ent :
			return [],[]

		refList = ent.refs(refKindStr, entKindStr, isUnique)
		entList = [refObj.ent() for refObj in refList]
		return entList, refList

	def searchRefObj(self, srcUName, tarUName):
		if not self._db:
			return None
		ent = self._db.lookup_uniquename(srcUName)
		if not ent:
			return None

		refList = ent.refs()
		for ref in refList:
			if ref.ent().uniquename() == tarUName:
				return ref
		return None

	def searchRef(self, uniqueName, refKindStr = None, entKindStr = None, isUnique = True):
		if not self._db:
			return []
		ent = self._db.lookup_uniquename(uniqueName)
		if not ent:
			return []

		refList = ent.refs(refKindStr, entKindStr, isUnique)
		return refList
	
	def searchCallPaths(self, srcUniqueName, tarUniqueName):
		# 返回值是 [entity 集合], [调用ref集合]
		if not srcUniqueName or not tarUniqueName or not self._db:
			return [],[]

		db = self._db
		class Vtx(object):
			def __init__(self, name):
				self.name = name
				self.isPathed = False		# 是否在路径之中
				self.adjNameList = []		# 所有相邻顶点
				self.curAdjIdx = 0			# 当前准备访问的相邻顶点
				self.ent = db.lookup_uniquename(name)

				# 找出调用的所有entity
				if self.ent:					
					refList = self.ent.refs('call, overriddenby', 'function, method', True)
					self.adjNameList = [(refObj.ent().uniquename(), refObj) for refObj in refList]

		vtxDict = {srcUniqueName: Vtx(srcUniqueName)}	# 存储访问过的节点
		vtxStack = [srcUniqueName]
		vtxSet = set()									# 存储最终路径经过的节点名称
		refSet = set()

		while len(vtxStack) > 0:
			topVtx = vtxDict[vtxStack[-1]]

			if topVtx.curAdjIdx >= len(topVtx.adjNameList):
				# 没有相邻节点可以访问了，从栈弹出
				vtxStack.pop()
			else:
				# 尝试访问相邻节点
				adjName = topVtx.adjNameList[topVtx.curAdjIdx][0]
				topVtx.curAdjIdx += 1

				# 路径不含环
				if adjName not in vtxStack:
					if adjName == tarUniqueName or (adjName in vtxDict and vtxDict[adjName].isPathed):
						# 到达已有路径,或到达终点，记录路径，加入新节点
						for v in vtxStack:
							vObj = vtxDict[v]
							vObj.isPathed = True
							vtxSet.add(v)
							adjObj = vObj.adjNameList[vObj.curAdjIdx-1]
							refSet.add((v, adjObj[0], adjObj[1]))
					elif adjName not in vtxDict:
						# 到达陌生节点,加入栈
						vtxDict[adjName] = Vtx(adjName)
						vtxStack.append(adjName)
					else:
						# 到达入过栈但现在不在栈的节点
						# 由于当一个节点出发的所有相邻节点都遍历完后，这个节点才会被从栈删除，所以此时这个节点无须再次进栈遍历
						pass

		vtxSet.discard(srcUniqueName)
		return list(vtxSet), list(refSet)

	def listFiles(self):
		if not self._db:
			return

		files = self._db.ents('file')

		for fileEnt in files:
			print(fileEnt.longname())

	def buildSymbolTree(self):
		if not self._db:
			return None, None

		# list all global objects
		entList = self._db.ents('class,struct,namespace,function')
		symbolDict = {}
		print (len(entList))
		nNoDefine = 0
		for ent in entList:
			if ent.kindname().lower().find('local') != -1:
				continue
			symbol = SymbolNode(ent.uniquename(), ent.name(), ent)
			symbolDict[ent.uniquename()] = symbol
		for uniname, symbol in symbolDict.items():
			ent = self._db.lookup_uniquename(uniname)
			if not ent:
				continue
			refList = ent.refs('declare,define')
			for ref in refList:
				refSymbol = symbolDict.get(ref.ent().uniquename())
				if not refSymbol:
					continue
				symbol.addChild(refSymbol)

			defineList = ent.refs('definein')
			if not defineList:
				defineList = ent.refs('declarein')
			if defineList:
				ref = defineList[0]
				fileName = ref.file().longname()
				symbol.setDefineFile(fileName)

		rootNode = SymbolNode('root','root', None)
		for uniname, symbol in symbolDict.items():
			if symbol.parent == None:
				rootNode.addChild(symbol)
		printSymbolDict(rootNode)
		return rootNode, symbolDict

	def _buildSymbolTreeRecursive(self, symbol):
		if not symbol:
			return

		symbolEnt = self._db.lookup_uniquename(symbol.uniqueName)
		if not symbolEnt:
			return

		# ignore function body
		kindStr = symbolEnt.kindname().lower()
		if kindStr.find('function') != -1 or kindStr.find('method') != -1:
			return

		refList = symbolEnt.refs('declare,define')
		for ref in refList:
			ent = ref.ent()
			childSymbol = SymbolNode(ent.uniquename(), ent.name(), ent)
			symbol.addChild(childSymbol)


def printSymbolDict(sym, indent = 0):
	for uname, childSym in sym.childrenDict.items():
		printSymbolDict(childSym, indent+1)

if __name__ == "__main__":
	db = CodeDB()
	db.open('I:/Programs/CodeAtlasProject/CodeView/vega.udb')
	#db.open('C:/Users/me/AppData/Roaming/Sublime Text 3/Packages/CodeAtlas/codeatlassublime.udb')
	#db.listFiles()
	root = db.buildSymbolTree()

	printSymbolDict(root)
	db.close()

