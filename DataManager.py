import sublime
from sublime_plugin import TextCommand, ApplicationCommand
from CodeAtlas.SocketThread import SocketThread

class DataManager(object):
	dataMgr = None
	def __init__(self):
		print('init data manager')
		# import traceback
		# traceback.print_stack()
		self.socket = SocketThread(('127.0.0.1', 12346),('127.0.0.1', 12345))

	@staticmethod
	def instance():
		if DataManager.dataMgr is None:
			DataManager.dataMgr = DataManager()
		return DataManager.dataMgr

	def getSocket(self):
		return self.socket