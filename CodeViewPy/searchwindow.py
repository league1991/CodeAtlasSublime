# -*- coding: utf-8 -*-
from PyQt4 import QtGui,QtCore,uic
import sys
import searchwindow
import math
from db.DBManager import DBManager

qtCreatorFile = './ui/Search.ui' # Enter file here.

Ui_SearchWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class ResultItem(QtGui.QListWidgetItem):
	def __init__(self, entity, parent = None):
		text = entity.longname()
		super(ResultItem, self).__init__(text, parent)
		self.uniqueName = entity.uniquename()

	def getUniqueName(self):
		return self.uniqueName

class SearchWindow(QtGui.QScrollArea, Ui_SearchWindow):
	def __init__(self, parent = None):
		QtGui.QScrollArea.__init__(self)
		Ui_SearchWindow.__init__(self)
		self.setupUi(self) 
		self.searchButton.clicked.connect(self.onSearch)
		self.addToSceneButton.clicked.connect(self.onAddToScene)


	def onSearch(self):
		searchWord = self.inputEdit.text()
		searchKind = self.kindEdit.text() 
		searchFile = self.fileEdit.text()
		searchLine = self.lineBox.value()
		db = DBManager.instance().getDB()
		if not db:
			return
		ents = db.search(searchWord, searchKind)

		self.resultList.clear()

		bestEntList = []
		if not ents:
			return
		for ent in ents:
			if ent and searchWord in ent.longname():
				bestEntList.append(ent)

		if searchFile and len(ents) < 100:
			entList = bestEntList
			bestEntList = []
			bestEntDist = []
			for ent in entList:
				refs = ent.refs()
				if not refs:
					continue
				fileNameSet = set()
				lineDist = 10000000
				for ref in refs:
					if not ref:
						continue
					fileEnt = ref.file()
					line = ref.line()
					column = ref.column()
					fileNameSet.add(fileEnt.longname())
					lineDist = min(lineDist, math.fabs(line - searchLine))

				if searchFile in fileNameSet:
					bestEntList.append(ent)
					bestEntDist.append(lineDist)

			if searchLine > -1:
				minDist = 10000000
				bestEnt = None
				for i, ent in enumerate(bestEntList):
					if bestEntDist[i] < minDist:
						minDist = bestEntDist[i]
						bestEnt = bestEntList[i]
				bestEntList = [bestEnt]

		bestItem = None
		for i, ent in enumerate(ents):
			if i > 200:
				break
			resItem = ResultItem(ent)
			if len(bestEntList) > 0 and ent == bestEntList[0] or len(bestEntList) == 1:
				bestItem = resItem
			self.resultList.addItem(resItem)
		if bestItem:
			self.resultList.setCurrentItem(bestItem)

	def onAddToScene(self):
		item = self.resultList.currentItem()

		from UIManager import UIManager
		scene = UIManager.instance().getScene()

		if not item or not scene:
			return

		scene.acquireLock()
		res, codeItem = scene.addCodeItem(item.getUniqueName())

		if codeItem:
			UIManager.instance().getScene().clearSelection()
			codeItem.setSelected(True)

		scene.releaseLock()

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	window = SearchWindow()
	window.show()
	sys.exit(app.exec_())