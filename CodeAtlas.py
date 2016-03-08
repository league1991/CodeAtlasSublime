import sublime
from sublime_plugin import TextCommand, ApplicationCommand
import os
import subprocess
from CodeAtlas.SocketThread import SocketThread
from CodeAtlas.DataManager import DataManager

class Start_atlas_Command(ApplicationCommand):
	def is_enabled(self):
		return True

	def run(self):
		curPath = os.path.split(os.path.realpath(__file__))[0]
		print('curPath ', curPath)
		
		subprocess.Popen(curPath + '\\codeView.bat', cwd = curPath)

		socketThread = DataManager.instance().getSocket()
		if not socketThread.isListening():
			socketThread.start()

class Open_database_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('onOpen', None)

class Update_database_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('onAnalyze', None)

class Show_in_atlas_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		fileName = self.view.file_name()
		print(fileName)

		for sel in self.view.sel():
			print('--------------------------------------')
			pnt = sel.a
			region = self.view.word(pnt)

			name = self.view.substr(region)
			scope = self.view.scope_name(pnt)
			print(name)
			print(scope)

			kind = '*'
			if scope.find('function') != -1:
				kind = 'function'
			elif scope.find('class') != -1:
				kind = 'class'
			socket.remoteCall('showInAtlas', {'n':name, 'f':fileName,'k':kind})

class Find_callers_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('onFindCallers', None)

class Find_callees_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('onFindCallees', None)

class Find_members_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('onFindMembers', None)

class Find_bases_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('onFindBases', None)

class Find_uses_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('onFindUses', None)

class Go_to_right_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('goToRight', None)

class Go_to_left_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('goToLeft', None)

class Go_to_up_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('goToUp', None)

class Go_to_down_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('goToDown', None)

class Go_to_up_right_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('goToUpRight', None)

class Go_to_down_right_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('goToDownRight', None)

class Go_to_down_left_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('goToDownLeft', None)

class Go_to_up_left_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('goToUpLeft', None)

class Delete_selected_items_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('onDeleteSelectedItems', None)

class Delete_oldest_items_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('onClearOldestItem', None)

class Test_Command(TextCommand):
	def run(self, edit):
		print('test')