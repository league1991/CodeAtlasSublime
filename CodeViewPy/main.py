import mainwindow
import sys
from PyQt4 import QtCore, QtGui, uic
from codescene import CodeScene
from UIManager import UIManager

if __name__ == "__main__":
	#print('main:', sys.argv)
	app = QtGui.QApplication(sys.argv)

	from db.DBManager import DBManager
	dbObj = DBManager.instance()
	uiObj = UIManager.instance()

	print('main')
	uiObj.showMainUI()
	dbObj.startSocket()

	w = uiObj.getMainUI()
	#w.move(app.desktop().width() *0.8,0);

	sys.exit(app.exec_())