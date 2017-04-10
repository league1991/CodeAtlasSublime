# -*- coding: utf-8 -*-
from PyQt4 import QtGui,QtCore,uic
import sys

qtCreatorFile = './ui/Symbol.ui' # Enter file here.

Ui_SymbolWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class ForbiddenItem(QtGui.QListWidgetItem):
	def __init__(self, uname, name, parent = None):
		super(ForbiddenItem, self).__init__(name, parent)
		self.uniqueName = uname

	def getUniqueName(self):
		return self.uniqueName

class SymbolWindow(QtGui.QScrollArea, Ui_SymbolWindow):
	def __init__(self, parent = None):
		QtGui.QScrollArea.__init__(self)
		Ui_SymbolWindow.__init__(self)
		self.setupUi(self)
		self.addForbidden.clicked.connect(self.onAddForbidden)
		self.deleteForbidden.clicked.connect(self.onDeleteForbidden)
		self.updateCommentButton.clicked.connect(self.updateComment)
		self.filterEdit.textEdited.connect(self.onTextEdited)

	def onTextEdited(self):
		self.updateForbiddenSymbol()

	def onAddForbidden(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		scene.addForbiddenSymbol()
		self.updateForbiddenSymbol()

	def updateForbiddenSymbol(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		forbidden = scene.getForbiddenSymbol()
		filter = self.filterEdit.text().lower()

		self.forbiddenList.clear()
		itemList = [ForbiddenItem(uname, name) for uname, name in forbidden.items() if filter in name.lower()]
		itemList.sort(key = lambda item: item.text().lower())
		for item in itemList:
			self.forbiddenList.addItem(item)


	def onDeleteForbidden(self):
		item = self.forbiddenList.currentItem()

		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if not item or not scene:
			return

		scene.acquireLock()
		scene.deleteForbiddenSymbol(item.getUniqueName())
		self.updateForbiddenSymbol()

		item = self.forbiddenList.item(0)
		if item:
			self.forbiddenList.setCurrentItem(item)

		scene.releaseLock()

	def updateSymbol(self, symbolName, comment = ''):
		self.symbolLabel.setText(symbolName)
		self.commentEdit.setPlainText(comment)

	def updateComment(self):
		text = self.commentEdit.toPlainText()
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		scene.updateSelectedComment(text)

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	window = SymbolWindow()
	window.show()
	sys.exit(app.exec_())