import mainwindow
import sys
from PyQt4 import QtCore, QtGui, uic
from codescene import CodeScene
from UIManager import UIManager

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)

	from db.DBManager import DBManager
	dbObj = DBManager.instance()
	uiObj = UIManager.instance()

	print('main')
	uiObj.showMainUI()
	dbObj.startSocket()

	sys.exit(app.exec_())