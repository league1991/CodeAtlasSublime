# -*- coding: utf-8 -*-
import sys
import os
from PyQt4 import QtCore, QtGui, Qt
#print sys.path
#sys.path.append('D:/Program Files (x86)/SciTools/bin/pc-win32/python')
import understand
import subprocess

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
		print('open', self._db)

	def close(self):
		if self._db:
			self._db.close()

	@QtCore.pyqtSlot()
	def reopen(self):
		if self._dbPath:
			self._db = understand.open(self._dbPath)

	def analyze(self):
		if self._db and self._dbPath:
			self._db.close()
			self._db = None

			cmdStr = r'und analyze "%s"' % self._dbPath
			print(cmdStr)
			workingPath = r'D:\Program Files (x86)\SciTools\bin\pc-win32'

			#os.system(cmdStr)
			p = subprocess.call(cmdStr, timeout= None, cwd = workingPath)
			#p.wait()

			print ('wait finish--------------------', self._dbPath)
			#self._db = understand.open(self._dbPath)
			self.reopenSignal.emit()
			print('open finish')

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
			return []
		ent = self._db.lookup_uniquename(uniqueName)
		if not ent :
			return []

		refList = ent.refs(refKindStr, entKindStr, isUnique)
		entList = [refObj.ent().uniquename() for refObj in refList]
		#print('entList', entList)
		return entList, refList

	def searchRef(self, uniqueName, refKindStr, entKindStr, isUnique = True):
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

		# print('src unique', srcUniqueName)
		# print('tar unique', tarUniqueName)
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
					refList = self.ent.refs('call', 'function', True)
					self.adjNameList = [(refObj.ent().uniquename(), refObj) for refObj in refList]

		vtxDict = {srcUniqueName: Vtx(srcUniqueName)}	# 存储访问过的节点
		vtxStack = [srcUniqueName]
		vtxSet = set()									# 存储最终路径经过的节点名称
		refSet = set()

		while len(vtxStack) > 0:
			topVtx = vtxDict[vtxStack[-1]]
			#print('stack:', [vtxDict[v].ent.name() for v in vtxStack])

			if topVtx.curAdjIdx >= len(topVtx.adjNameList):
				# 没有相邻节点可以访问了，从栈弹出
				vtxStack.pop()
			else:
				# 尝试访问相邻节点
				adjName = topVtx.adjNameList[topVtx.curAdjIdx][0]
				topVtx.curAdjIdx += 1
				# print('adj:', adjName)
				# print('tar:', tarUniqueName)
				# print('is-----', adjName == tarUniqueName)

				# 路径不含环
				if adjName not in vtxStack:
					if adjName == tarUniqueName or (adjName in vtxDict and vtxDict[adjName].isPathed):
						# 到达已有路径,或到达终点，记录路径，加入新节点
						#print('--- add node ---')
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

		#print('search end', vtxSet, refSet)
		vtxSet.discard(srcUniqueName)
		return list(vtxSet), list(refSet)


