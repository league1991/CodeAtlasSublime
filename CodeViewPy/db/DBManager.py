import db.CodeDB as CodeDB

class DBManager(object):
	dbMgr = None

	def __init__(self):
		self.db = CodeDB.CodeDB()
		from SocketThread import SocketThread
		self.socket = SocketThread(('127.0.0.1', 12345),('127.0.0.1', 12346))
		self.socket.start()

	@staticmethod
	def instance():
		if DBManager.dbMgr is None:
			DBManager.dbMgr = DBManager()

		return DBManager.dbMgr

	def getDB(self):
		return self.db

	def getSocket(self):
		return self.socket