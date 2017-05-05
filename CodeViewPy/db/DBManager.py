# -*- coding: utf-8 -*-

class DBManager(object):
	dbMgr = None
	atlasPort = 12346
	sublimePort = 12345
	def __init__(self):
		import db.CodeDB as CodeDB
		import db.DoxygenDB as DoxygenDB
		from SocketThread import SocketThread
		#self.db = CodeDB.CodeDB()
		self.db = DoxygenDB.DoxygenDB()
		self.socket = SocketThread(('127.0.0.1', self.atlasPort),('127.0.0.1', self.sublimePort))

	@staticmethod
	def instance():
		if DBManager.dbMgr is None:
			DBManager.dbMgr = DBManager()

		return DBManager.dbMgr

	def openDB(self, path):
		import db.DoxygenDB as DoxygenDB
		if path.strip().endswith('udb'):
			import db.CodeDB as CodeDB
			self.db = CodeDB.CodeDB()
		else:
			import db.DoxygenDB as DoxygenDB
			self.db = DoxygenDB.DoxygenDB()

		self.db.open(path)
		self._onOpen()

	def analysisDB(self):
		self.db.analyze()
		self._onOpen()

	def getDB(self):
		return self.db

	def getSocket(self):
		return self.socket

	def startSocket(self):
		self.socket.start()

	def _onOpen(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		scene.onOpenDB()

		mainUI = UIManager.instance().getMainUI()
		mainUI.symbolDock.widget().updateForbiddenSymbol()
		mainUI.schemeDock.widget().updateScheme()