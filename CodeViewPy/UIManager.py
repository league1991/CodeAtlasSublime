import mainwindow
import sys
from PyQt5 import QtCore, QtGui, uic
from codescene import CodeScene
from SymbolScene import SymbolScene

class UIManager(object):
	uiMgr = None
	def __init__(self):
		self.scene = CodeScene()
		self.symScene = SymbolScene()
		self.mainUI = None
		self.uiSetting = UISettings()

	@staticmethod
	def instance():
		if UIManager.uiMgr is None:
			UIManager.uiMgr = UIManager()
		return UIManager.uiMgr

	def getMainUI(self):
		return self.mainUI

	def showMainUI(self):
		if not self.mainUI:
			UIManager.uiMgr.mainUI = mainwindow.MainUI()
		self.mainUI.show()

	def getScene(self):
		return self.scene

	def getSymbolScene(self):
		return self.symScene

	def getUISetting(self):
		return self.uiSetting

class UISettings(object):
	def __init__(self):
		pass

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)

	from db.DBManager import DBManager
	dbObj = DBManager.instance()
	uiObj = UIManager.instance()

	uiObj.showUI()

	sys.exit(app.exec_())