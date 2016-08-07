# -*- coding: utf-8 -*-
from PyQt4 import QtGui,QtCore,uic
import sys

qtCreatorFile = './ui/Scheme.ui' # Enter file here.

Ui_SymbolWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class SchemeItem(QtGui.QListWidgetItem):
	def __init__(self, name, parent = None):
		super(SchemeItem, self).__init__(name, parent)
		self.uniqueName = name

	def getUniqueName(self):
		return self.uniqueName

class SchemeWindow(QtGui.QScrollArea, Ui_SymbolWindow):
	def __init__(self, parent = None):
		QtGui.QScrollArea.__init__(self)
		Ui_SymbolWindow.__init__(self)
		self.setupUi(self)
		self.addSchemeButton.clicked.connect(self.onAddOrModifyScheme)
		self.showSchemeButton.clicked.connect(self.onShowScheme)
		self.deleteSchemeButton.clicked.connect(self.onDeleteScheme)
		self.schemeList.currentItemChanged.connect(self.onSchemeChanged)

	def onSchemeChanged(self, currentItem, prevItem):
		if currentItem:
			self.nameEdit.setText(currentItem.getUniqueName())

	def onAddOrModifyScheme(self):
		schemeName = self.nameEdit.text()
		if not schemeName:
			return

		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		scene.addOrReplaceScheme(schemeName)
		self.updateScheme()

	def onShowScheme(self):
		item = self.schemeList.currentItem()
		schemeName = item.getUniqueName()
		if not schemeName:
			return

		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		scene.acquireLock()
		scene.showScheme(schemeName)
		scene.releaseLock()
		self.updateScheme()

	def onDeleteScheme(self):
		item = self.schemeList.currentItem()
		if not item:
			return

		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		scene.deleteScheme(item.getUniqueName())
		self.updateScheme()

	def updateScheme(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		nameList = scene.getSchemeNameList()

		self.schemeList.clear()
		for name in nameList:
			self.schemeList.addItem(SchemeItem(name))
