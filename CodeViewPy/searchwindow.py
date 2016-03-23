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
		ents = db.search(searchWord, searchKind)

		while self.resultList.count() > 0:
			self.resultList.takeItem(0)

		bestEntList = []
		for ent in ents:
			if ent.name() == searchWord:
				bestEntList.append(ent)
			#print('ent', ent.name(), ent.longname(), searchWord, type(ent.name), type(searchWord))
 
		#print('best ent list 1', bestEntList)
		if searchFile: 
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
					fileEnt = ref.file()
					line = ref.line()
					column = ref.column()
					fileNameSet.add(fileEnt.longname())
					lineDist = min(lineDist, math.fabs(line - searchLine))

				#print('searchfile', searchFile, 'fileNameSet', fileNameSet)
				if searchFile in fileNameSet:
					bestEntList.append(ent)
					bestEntDist.append(lineDist)

			#print('best ent list before line', bestEntList, bestEntDist)
			if searchLine > -1:
				minDist = 10000000
				bestEnt = None
				for i, ent in enumerate(bestEntList):
					if bestEntDist[i] < minDist:
						minDist = bestEntDist[i]
						bestEnt = bestEntList[i]
				bestEntList = [bestEnt]
				#print('best ent list line', bestEntList)

		bestItem = None
		print('before add item')
		for ent in ents:
			resItem = ResultItem(ent)
			if len(bestEntList) > 0 and ent == bestEntList[0]:
				bestItem = resItem
			self.resultList.addItem(resItem)
		print('best item', bestItem, bestEntList)
		if bestItem:
			self.resultList.setCurrentItem(bestItem)

		print('end search')

	def onAddToScene(self):
		# if self.resultList.count() == 1:
		# 	print('before set cur row')
		# 	self.resultList.setCurrentRow(0)
		item = self.resultList.currentItem()

		from UIManager import UIManager
		scene = UIManager.instance().getScene()

		if not item or not scene:
			return

		print('before code item')
		res, codeItem = scene.addCodeItem(item.getUniqueName())
		print('add code item')

		if codeItem:
			UIManager.instance().getScene().clearSelection()
			codeItem.setSelected(True)

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	window = SearchWindow()
	window.show()
	sys.exit(app.exec_())