import sublime
from sublime_plugin import TextCommand, ApplicationCommand,EventListener
import os
import time
import subprocess
from CodeAtlas.SocketThread import SocketThread
from CodeAtlas.DataManager import DataManager

class Start_atlas_Command(ApplicationCommand):
	def is_enabled(self):
		return True
 
	def run(self):
		curPath = os.path.split(os.path.realpath(__file__))[0] 
		print('curPath ', curPath)		
		subprocess.Popen(curPath + '\\codeView.bat', cwd = curPath, stdout = None)
		 
		#curPath = curPath + '\\CodeViewPy'
		#subprocess.Popen('main', cwd = curPath, shell = True )

		socketThread = DataManager.instance().getSocket()
		if not socketThread.isListening():
			socketThread.start()

class Open_database_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('onOpen', None)

class Analyze_database_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('onAnalyze', None)

class Show_scheme_1_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('showScheme',[1])

class Show_scheme_2_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('showScheme',[2])

class Show_scheme_3_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('showScheme',[3])

class Show_scheme_4_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('showScheme',[4])

class Show_scheme_5_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('showScheme',[5])

class Show_scheme_6_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('showScheme',[6])

class Show_scheme_7_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('showScheme',[7])

class Show_scheme_8_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('showScheme',[8])

class Show_scheme_9_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('showScheme',[9])

class Show_in_atlas_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		fileName = self.view.file_name()
		print(fileName)

		for sel in self.view.sel():
			print('--------------------------------------')
			pnt = sel.a
			region = self.view.word(sel)

			name = self.view.substr(region)
			if self.view.substr(self.view.word(region.a-1)) == '::':
				className = self.view.substr(self.view.word(region.a-2))
				if className:
					name = className + '::' + name
			elif self.view.substr(self.view.word(region.b+1)) == '::':
				funcName = self.view.substr(self.view.word(region.b+2))
				if funcName:
					name = name + '::' + funcName

			scope = self.view.scope_name(pnt)
			line = self.view.rowcol(region.a)[0]+1
 
			kind = '*'
			if scope.find('variable') != -1:
				kind = 'variable'
			elif scope.find('function') != -1:
				kind = 'function'
			elif scope.find('class') != -1:
				kind = 'class'
			# socket.remoteCall('showInAtlas', {'n':name, 'f':fileName,'k':kind, 'l':line})
			socket.remoteCall('showInAtlas', [name, kind, fileName, line])

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

class Delete_and_ignore_selected_items_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('onDeleteSelectedItemsAndAddToStop', None)

class Delete_oldest_items_Command(TextCommand):
	def run(self, edit):
		socket = DataManager.instance().getSocket()
		socket.remoteCall('onClearOldestItem', None)

class Test_Command(TextCommand):
	def run(self, edit):
		print('test')

class SelectionListener(EventListener):
	lastTime = -1
	#def on_selection_modified(self, view):
	def on_modified(self, view):
		#print('selection modified--------------------------------------------')
		if time.time() - SelectionListener.lastTime < 2:
			return

		SelectionListener.lastTime = time.time()
		regions = view.find_by_selector('entity.name.function')
		nameSet = set()
		line = -1
		for sel in view.sel():
			#print('--------------------------------------')
			pnt = sel.b

			bestRegion = None
			bestDist = 100000000
			for region in regions:
				dist = pnt - region.a
				if dist > 0 and dist < bestDist:
					bestDist = dist
					bestRegion = region
			if not bestRegion:
				continue
			name = view.substr(bestRegion)
			scopeName = view.scope_name((bestRegion.a+bestRegion.b)/2)
			line = view.rowcol((bestRegion.a+bestRegion.b)/2)[0]+1
			nameSet.add(name)
 
		if len(nameSet) == 1: 
			name = list(nameSet)[0]
			socket = DataManager.instance().getSocket()
			fileName = view.file_name()
			# socket.remoteCall('showInAtlas', {'n':name, 'f':fileName,'k':'function','l':line})
			socket.remoteCall('showInAtlas', [name, fileName, 'function', line])