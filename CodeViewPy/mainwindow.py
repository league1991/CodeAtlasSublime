# MianWindow.py
#!/usr/bin/env python
#coding=utf-8

import sys

from PyQt4 import QtCore, QtGui, uic

import codeview
from callview import CallView
from symbolview import SymbolView
from symbolwindow import SymbolWindow
from schemewindow import SchemeWindow
from searchwindow import SearchWindow
import random
import ui.CodeUIItem as CodeUIItem
import db.DBManager as DBManager
from json import *


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
		self.actionFindCallPaths.triggered.connect(self.onFindCallPaths)
		self.actionGoUp.triggered.connect(self.goToUp)
		self.actionGoDown.triggered.connect(self.goToDown)
		self.actionGoLeft.triggered.connect(self.goToLeft)
		self.actionGoRight.triggered.connect(self.goToRight)

		self.actionUpdatePosition.triggered.connect(self.onUpdatePosition)
		self.actionDeleteOldItems.triggered.connect(self.onDeleteOldItems)
		self.actionDeleteSelectedItems.triggered.connect(self.onDeleteSelectedItems)
		self.actionDeleteAndIgnoreSelectedItems.triggered.connect(self.onDeleteSelectedItemsAndAddToStop)
		self.actionShowSymbolWindow.triggered.connect(self.onActionShowSymbolWindow)
		self.actionShowSearchWindow.triggered.connect(self.onActionShowSearchWindow)
		self.actionBuildSymbolScene.triggered.connect(self.onBuildSymbolScene)
		self.actionPinSymbol.triggered.connect(self.onPinSymbol)
		self.actionUnpinSymbol.triggered.connect(self.onUnpinSymbol)
		self.actionIgnoreSymbol.triggered.connect(self.onIgnoreSymbol)
		self.actionUnignoreSymbol.triggered.connect(self.onUnignoreSymbol)
		self.setCentralWidget(codeview.CodeView())
		self.symbolView = None

		self.searchDock = QtGui.QDockWidget()
		self.searchDock.setWidget(SearchWindow())
		self.searchDock.setWindowTitle('Search')

		self.symbolDock = QtGui.QDockWidget()
		self.symbolDock.setWidget(SymbolWindow())
		self.symbolDock.setWindowTitle('Symbol')

		self.schemeDock = QtGui.QDockWidget()
		self.schemeDock.setWidget(SchemeWindow())
		self.schemeDock.setWindowTitle('Scheme')

		self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.symbolDock)
		self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.searchDock)
		self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.schemeDock)
		self.tabifyDockWidget(self.symbolDock, self.searchDock)
		self.tabifyDockWidget(self.searchDock, self.schemeDock)
		self.searchDock.setVisible(False)
		self.symbolDock.setVisible(False)
		self.schemeDock.setVisible(False)

	def closeEvent(self, event):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		scene.onCloseDB()

	def onActionShowSearchWindow(self):
		visible = self.searchDock.isVisible()
		self.searchDock.setVisible(not visible)
		self.symbolDock.setVisible(not visible)
		self.schemeDock.setVisible(not visible)

	def onBuildSymbolScene(self):
		from UIManager import UIManager
		symScene = UIManager.instance().getSymbolScene()
		symScene.buildScene()

	def onIgnoreSymbol(self):
		from UIManager import UIManager
		scene = UIManager.instance().getSymbolScene()
		if scene:
			scene.ignoreSymbol(True)

	def onUnignoreSymbol(self):
		from UIManager import UIManager
		scene = UIManager.instance().getSymbolScene()
		if scene:
			scene.ignoreSymbol(False)

	def onPinSymbol(self):
		from UIManager import UIManager
		scene = UIManager.instance().getSymbolScene()
		if scene:
			scene.pinSymbol(True)

	def onUnpinSymbol(self):
		from UIManager import UIManager
		scene = UIManager.instance().getSymbolScene()
		if scene:
			scene.pinSymbol(False)

	def onActionShowSymbolWindow(self):
		self.symbolView = SymbolView()
		#self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.symbolView)
		self.symbolView.show()

	@QtCore.pyqtSlot(str)
	def onSocketEvent(self, dataStr):
		from UIManager import UIManager

		dataObj = JSONDecoder().decode(dataStr)

		funName = dataObj.get('f')
		paramDict = dataObj.get('p', None)
		mainUI = self
		scene = UIManager.instance().getScene()
		funObj = getattr(mainUI, funName)
		if funObj:
			scene.acquireLock()
			if paramDict is None:
				funObj()
			else:
				funObj(paramDict)
			scene.releaseLock()

	def getItemMenu(self):
		return self.menuItem

	def getSymbolMenu(self):
		return self.menuSymbol

	def getSymbolWidget(self):
		return self.symbolDock.widget()

	def getView(self):
		return self.centralWidget()

	def getScene(self):
		return self.getView().scene()

	def onFindCallPaths(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		scene.addCallPaths()

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
		curPath = curDir.currentPath()
		dbPath = dialog.getOpenFileName(self, 'Open Database', curDir.currentPath())
		if dbPath:
			print(dbPath)
			dbmgr = DBManager.DBManager.instance()
			dbmgr.getDB().open(dbPath)

			from UIManager import UIManager
			symScene = UIManager.instance().getSymbolScene()
			#symScene.buildScene()

	def onOpenPath(self, param):
		dialog = QtGui.QFileDialog()
		curDir = QtCore.QDir()
		curPath = curDir.currentPath()
		if param and False:
			curPath = param[0]
		dbPath = dialog.getOpenFileName(self, 'Open Database', curPath)
		#dbPath = r'I:/Programs/test/myTest1/test1.udb'
		if dbPath:
			print(dbPath)
			dbmgr = DBManager.DBManager.instance()
			dbmgr.getDB().open(dbPath)
			from UIManager import UIManager
			symScene = UIManager.instance().getSymbolScene()
			#symScene.buildScene()

	def onTest(self):
		#import os
		#defaultPath = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + r'\CodeAtlasSublime.udb'
		#print(defaultPath)
		dbmgr = DBManager.DBManager.instance()
		defaultPath = r'C:\Users\me\AppData\Roaming\Sublime Text 3\Packages\CodeAtlas\CodeAtlasSublime.udb'
		#defaultPath = r'I:\Programs\autodesk\rapidrt-master\rapidRT.udb'
		dbmgr.getDB().open(defaultPath)

		from UIManager import UIManager
		symScene = UIManager.instance().getSymbolScene()
		#symScene.buildScene()

	def onFindCallers(self):
		self.findRefs('callby','function, method')

	def onFindCallees(self):
		self.findRefs('call','function, method', True)

	def onFindMembers(self):
		self.findRefs('declare,define','function, variable, object', True)

	def onFindBases(self):
		self.findRefs('base','class',False)
		self.findRefs('derive','class',True)

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
			scene.deleteSelectedItems(False)

	def onDeleteSelectedItemsAndAddToStop(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.deleteSelectedItems(True)
			mainUI = UIManager.instance().getMainUI()
			mainUI.symbolDock.widget().updateForbiddenSymbol()

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
		return self.searchDock.widget()

	def showScheme(self, param):
		ithScheme = param[0]-1
		isSelected = False
		if len(param) >= 2:
			isSelected = param[1]
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.showIthScheme(ithScheme, isSelected)

	def showInAtlas(self, param):
		#name = param.get('n','')
		#kind = param.get('k','')
		#fileName = param.get('f','')
		#line = param.get('l',-1)
		name = param[0]
		kind = param[1]
		fileName = param[2]
		line = param[3]

		if not name:
			return
		if not kind:
			kind = '*'
		if line == None:
			line = -1
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