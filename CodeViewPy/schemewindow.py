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
		self.filterEdit.textEdited.connect(self.onTextEdited)

	def onTextEdited(self):
		self.updateScheme()

	def onSchemeChanged(self, currentItem, prevItem):
		if currentItem:
			self.nameEdit.setText(currentItem.getUniqueName())

	def onAddOrModifyScheme(self):
		schemeName = self.nameEdit.text()
		if not schemeName:
			return

		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		schemeNameList = scene.getSchemeNameList()
		isAdd = True
		if schemeName in schemeNameList:
			button = QtGui.QMessageBox.question(self, "Add Scheme",
												"\"%s\" already exists. Replace it?" % schemeName,
												QtGui.QMessageBox.Ok | QtGui.QMessageBox.No)
			if button != QtGui.QMessageBox.Ok:
				isAdd = False

		if isAdd:
			scene.addOrReplaceScheme(schemeName)
			self.updateScheme()

	def onShowScheme(self):
		item = self.schemeList.currentItem()
		if not item:
			QtGui.QMessageBox.warning(self, "Warning", "Please select an item to show.")
			return

		schemeName = item.getUniqueName()
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		scene.acquireLock()
		scene.showScheme(schemeName, True)
		scene.releaseLock()
		self.updateScheme()

	def onDeleteScheme(self):
		item = self.schemeList.currentItem()
		if not item:
			QtGui.QMessageBox.warning(self, "Warning", "Please select an item to delete.")
			return

		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		scene.deleteScheme(item.getUniqueName())
		self.updateScheme()

	def updateScheme(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		nameList = scene.getSchemeNameList()
		filter = self.filterEdit.text().lower()

		self.schemeList.clear()
		for name in nameList:
			if filter in name.lower():
				self.schemeList.addItem(SchemeItem(name))
