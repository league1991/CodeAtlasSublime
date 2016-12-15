import db.CodeDB as CodeDB

class DBManager(object):
	dbMgr = None
	atlasPort = 12346
	sublimePort = 12345
	def __init__(self):
		self.db = CodeDB.CodeDB()
		from SocketThread import SocketThread
		self.socket = SocketThread(('127.0.0.1', self.atlasPort),('127.0.0.1', self.sublimePort))

	@staticmethod
	def instance():
		if DBManager.dbMgr is None:
			DBManager.dbMgr = DBManager()

		return DBManager.dbMgr

	def getDB(self):
		return self.db

	def getSocket(self):
		return self.socket

	def startSocket(self):
		self.socket.start()