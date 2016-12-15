import sublime
from sublime_plugin import TextCommand, ApplicationCommand
from CodeAtlas.SocketThread import SocketThread

class DataManager(object):
	dataMgr = None
	def __init__(self):
		print('init data manager')
		# import traceback
		# traceback.print_stack()
		self.sublimePort = 12345
		self.nextAtlasPort = 12346
		self.socketDict = {}

	@staticmethod
	def instance():
		if DataManager.dataMgr is None:
			DataManager.dataMgr = DataManager()
		return DataManager.dataMgr

	def getSocket(self, windowID = 0):
		if not self.socketDict.get(windowID):
			socket = SocketThread(('127.0.0.1', self.sublimePort),('127.0.0.1', self.nextAtlasPort))
			socket.windowID = windowID
			self.nextAtlasPort += 2
			self.sublimePort   += 2
			self.socketDict[windowID] = socket
		return self.socketDict[windowID]