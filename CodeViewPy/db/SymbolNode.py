# -*- coding: utf-8 -*-
import sys
import os
#print sys.path
#sys.path.append('D:/Program Files (x86)/SciTools/bin/pc-win32/python')
import understand
import subprocess
from db.SymbolAttr import SymbolAttr, createAttr

class FileData(object):
	def __init__(self):
		pass

class SymbolNode(object):
	KIND_NAMESPACE = 0
	KIND_CLASS = 1
	KIND_FUNCTION = 2
	KIND_VARIABLE = 3
	KIND_UNKNOWN  = 4

	Kind_Dict = {KIND_NAMESPACE: 'namespace', KIND_CLASS: 'class', KIND_VARIABLE: 'variable', KIND_FUNCTION: 'function', KIND_UNKNOWN: 'unknown'}
	def __init__(self, uniqueName, name, entity):
		self.uniqueName = uniqueName
		self.name = name
		self.kind = self.KIND_UNKNOWN
		if entity:
			kindStr = entity.kindname().lower()
			if kindStr.find('function') != -1 or kindStr.find('method') != -1:
				self.kind = self.KIND_FUNCTION
			elif kindStr.find('attribute') != -1 or kindStr.find('variable') != -1 or kindStr.find('object') != -1:
				self.kind = self.KIND_VARIABLE
			elif kindStr.find('class') != -1 or kindStr.find('struct') != -1:
				self.kind = self.KIND_CLASS
			elif kindStr.find('namespace') != -1:
				self.kind = self.KIND_NAMESPACE
			else:
				self.kind = self.KIND_UNKNOWN

		self.childrenDict = {}
		self.attrList = [None] * SymbolAttr.ATTR_NUM
		self.parent = None
		self.defineFile = ''

	def setDefineFile(self, fileName):
		self.defineFile = fileName

	def getKind(self):
		return self.kind

	def getKindName(self):
		return self.Kind_Dict[self.kind]

	def addChild(self, node):
		self.childrenDict[node.uniqueName] = node
		node.parent = self

	def addAttr(self, attrType, attrObj):
		self.attrList[attrType] = attrObj
		attrObj.node = self

	def getOrAddAttr(self, attrType):
		attr = self.attrList[attrType]
		if attr:
			return attr
		attrObj = createAttr(attrType)
		self.attrList[attrType] = attrObj
		return attrObj

	def getAttr(self, attrType):
		return self.attrList[attrType]

	def addUIItem(self, uiItem):
		self.attrList[self.ATTR_UIITEM] = uiItem
		uiItem.node = self

	def getChildDict(self):
		return self.childrenDict

	def isLeaf(self):
		return len(self.childrenDict) == 0
