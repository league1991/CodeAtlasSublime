# MianWindow.py
#!/usr/bin/env python
#coding=utf-8

import sys

from PyQt4 import QtCore, QtGui, uic

import codeview
import random
import ui.CodeUIItem as CodeUIItem
import db.DBManager as DBManager


qtCreatorFile = './ui/mainwindow.ui' # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class MainUI(QtGui.QMainWindow, Ui_MainWindow):
	def __init__(self):
		QtGui.QMainWindow.__init__(self)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)
		self.actionOpen.triggered.connect(self.onOpen)
		self.actionAnalyze.triggered.connect(self.onAnalyze)
		self.actionTest.triggered.connect(self.onTest)
		self.actionFindCallers.triggered.connect(self.onFindCallers)
		self.actionFindCallees.triggered.connect(self.onFindCallees)
		self.actionFindMembers.triggered.connect(self.onFindMembers)
		self.actionFindBases.triggered.connect(self.onFindBases)
		self.actionFindUses.triggered.connect(self.onFindUses)
		self.actionGoToEditor.triggered.connect(self.goToEditor)
		self.actionDeleteOldestItem.triggered.connect(self.onClearOldestItem)
		self.actionToggleFocus.triggered.connect(self.onToggleFocus)

		self.actionUpdatePosition.triggered.connect(self.onUpdatePosition)
		self.actionDeleteOldItems.triggered.connect(self.onDeleteOldItems)
		self.actionDeleteSelectedItems.triggered.connect(self.onDeleteSelectedItems)
		self.setCentralWidget(codeview.CodeView())


	def getItemMenu(self):
		return self.menuItem

	def getView(self):
		return self.centralWidget()

	def getScene(self):
		return self.getView().scene()

	def onToggleFocus(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		scene.autoFocusToggle = not scene.autoFocusToggle

	def onUpdatePosition(self):
		from UIManager import UIManager
		for i in range(5):
			UIManager.instance().getScene().updatePos()

	def onAnalyze(self):
		dbmgr = DBManager.DBManager.instance()
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.acquireLock()
			dbmgr.getDB().analyze()
			#dbmgr.getDB().open(r'C:\Users\me\AppData\Roaming\Sublime Text 3\Packages\CodeAtlas\CodeAtlasSublime.udb')
			print('before release')
			scene.releaseLock()
			print('after release')

	def onOpen(self):
		dialog = QtGui.QFileDialog()
		curDir = QtCore.QDir()
		dbPath = dialog.getOpenFileName(self, 'Open Database', curDir.currentPath())
		if dbPath:
			dbmgr = DBManager.DBManager.instance()
			dbmgr.getDB().open(dbPath)

	def onTest(self):
		import os
		defaultPath = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + r'\CodeAtlasSublime.udb'
		print(defaultPath)
		dbmgr = DBManager.DBManager.instance()
		dbmgr.getDB().open(defaultPath)

	def onFindCallers(self):
		self.findRefs('callby','function')

	def onFindCallees(self):
		self.findRefs('call','function', True)

	def onFindMembers(self):
		self.findRefs('declare,define','function, variable', True)

	def onFindBases(self):
		self.findRefs('base','class',True)

	def onFindUses(self):
		self.findRefs('declarein,definein,useby', 'function,class')

	def findRefs(self, refStr, entStr, inverseEdge = False):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		scene.addRefs(refStr, entStr, inverseEdge)

	def onDeleteSelectedItems(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.deleteSelectedItems()

	def onDeleteOldItems(self):
		from UIManager import UIManager
		from db.DBManager import DBManager

		scene = UIManager.instance().getScene()
		if scene:
			scene.clearUnusedItems()

	def onClearOldestItem(self):
		print('on clear oldest item')
		from UIManager import UIManager
		print('import ui manager', UIManager)
		from db.DBManager import DBManager
		print('import db manager', DBManager)

		scene = UIManager.instance().getScene()
		print('scene', scene)
		if scene:
			print('clear old item')
			scene.clearOldItem()

	def getSearchWindow(self):
		return self.searchWidget

	def showInAtlas(self, param):
		name = param.get('n','')
		kind = param.get('k','')
		fileName = param.get('f','')
		line = param.get('l',-1)
		#print('show in atlas', param)
		sw = self.getSearchWindow()
		sw.inputEdit.setText(name)
		sw.kindEdit.setText(kind)
		sw.fileEdit.setText(fileName)
		sw.lineBox.setValue(line)
		print('search')
		sw.onSearch()
		print('add to scene')
		sw.onAddToScene()

	def goToEditor(self):
		#print('go to editor')
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.showInEditor()

	def goToRight(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.findNeighbour((1.0,0.0))

	def goToLeft(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.findNeighbour((-1.0,0.0))

	def goToUp(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.findNeighbour((0.0,-1.0))

	def goToDown(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.findNeighbour((0.0,1.0))

	def goToUpRight(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.findNeighbour((1.0,-1.0))

	def goToDownRight(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.findNeighbour((1.0,1.0))

	def goToDownLeft(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.findNeighbour((-1.0,1.0))

	def goToUpLeft(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.findNeighbour((-1.0,-1.0))

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	window = MainUI()
	window.show()
	sys.exit(app.exec_())