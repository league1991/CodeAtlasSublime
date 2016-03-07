# -*- coding: utf-8 -*-
from PyQt4 import QtGui,QtCore,uic
import sys
import searchwindow
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
		db = DBManager.instance().getDB()
		ents = db.search(searchWord, searchKind)

		#print(ents)
		while self.resultList.count() > 0:
			self.resultList.takeItem(0)

		bestEnt = None
		for ent in ents:
			if ent.name() == searchWord:
				bestEnt = ent
			print('ent', ent.name(), ent.longname(), searchWord, type(ent.name), type(searchWord))

		bestItem = None
		for ent in ents:
			resItem = ResultItem(ent)
			if ent == bestEnt:
				bestItem = resItem
			self.resultList.addItem(resItem)
		print('best item', bestItem, bestEnt)
		if bestItem:
			self.resultList.setCurrentItem(bestItem)

	def onAddToScene(self):
		if self.resultList.count() == 1:
			self.resultList.setCurrentRow(0)
		item = self.resultList.currentItem()

		from UIManager import UIManager
		scene = UIManager.instance().getScene()

		if not item:
			return

		res, item = scene.addCodeItem(item.getUniqueName())

		if item:
			UIManager.instance().getScene().clearSelection()
			item.setSelected(True)
			for view in scene.views():
				view.centerOn(item)
				#view.setFocus()
				view.invalidateScene()
				#view.viewport().update()



if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	window = SearchWindow()
	window.show()
	sys.exit(app.exec_())