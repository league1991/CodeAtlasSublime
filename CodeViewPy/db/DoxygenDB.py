# -*- coding: utf-8 -*-
import sys
import os
from PyQt4 import QtCore, QtGui, Qt
import subprocess
from db.SymbolNode import FileData, SymbolNode

class DoxygenDB(QtCore.QObject):
	reopenSignal = QtCore.pyqtSignal()
	def __init__(self):
		super(DoxygenDB, self).__init__()
		self._db = None
		self._dbPath = ''
		self.reopenSignal.connect(self.reopen, Qt.Qt.QueuedConnection)

	def open(self, path):
		pass

	def getDBPath(self):
		return self._dbPath

	def close(self):
		pass

	@QtCore.pyqtSlot()
	def reopen(self):
		pass

	def analyze(self):
		pass

	def onOpen(self):
		pass

	def search(self, name, kindstring = None):
		pass

	def searchFromUniqueName(self, uniqueName):
		pass

	def searchRefEntity(self, uniqueName, refKindStr, entKindStr, isUnique = True):
		return [],[]

	def searchRefObj(self, srcUName, tarUName):
		return None

	def searchRef(self, uniqueName, refKindStr, entKindStr, isUnique = True):
		return []
	
	def searchCallPaths(self, srcUniqueName, tarUniqueName):
		return [],[]

	def listFiles(self):
		return

	def buildSymbolTree(self):
		return None, None

	def _buildSymbolTreeRecursive(self, symbol):
		return


def printSymbolDict(sym, indent = 0):
	for uname, childSym in sym.childrenDict.items():
		printSymbolDict(childSym, indent+1)

if __name__ == "__main__":
	db = DoxygenDB()
	db.open('I:/Programs/CodeAtlasProject/CodeView/vega.udb')
	#db.open('C:/Users/me/AppData/Roaming/Sublime Text 3/Packages/CodeAtlas/codeatlassublime.udb')
	#db.listFiles()
	#root = db.buildSymbolTree()

	#printSymbolDict(root)
	#db.close()

