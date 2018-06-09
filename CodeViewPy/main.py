import sys
from PyQt5 import QtGui, QtWidgets
from UIManager import UIManager

if __name__ == "__main__":
	print('argv:', sys.argv)
	app = QtWidgets.QApplication(sys.argv)

	from db.DBManager import DBManager
	if len(sys.argv) > 1:
		DBManager.atlasPort = int(sys.argv[1])
		DBManager.sublimePort = int(sys.argv[1])-1
	dbObj = DBManager.instance()
	uiObj = UIManager.instance()

	print('main')
	uiObj.showMainUI()
	dbObj.startSocket()

	w = uiObj.getMainUI()
	sys.exit(app.exec_())