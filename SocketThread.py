import socket
import threading
import time
import inspect
import ctypes
from json import *

class SocketThread(threading.Thread):
	def __init__(self, myAddress, remoteAddress):
		print('init socket')
		# import traceback
		# traceback.print_stack()
		
		threading.Thread.__init__(self)
		self.myAddress = myAddress
		self.remoteAddress = remoteAddress
		self.socketObj = None

	def isListening(self):
		return self.socketObj is not None

	def run(self):
		print('run', self.name)
		address = self.myAddress
		self.socketObj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socketObj.bind(address)

		while True:
			data, addr = self.socketObj.recvfrom(1024 * 5)
			dataStr = data.decode()
			dataObj = JSONDecoder().decode(dataStr)

			funName = dataObj.get('f')
			paramDict = dataObj.get('p')
			print('recv:', funName, paramDict)
			funObj = getattr(self, funName)
			if funObj:
				funObj(paramDict)

		print ('close socket')
		self.socketObj.close()

	def stop(self):
		def _async_raise(tid, exctype):
			"""raises the exception, performs cleanup if needed"""
			if not inspect.isclass(exctype):
				exctype = type(exctype)
			res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
			print('terminate connection thread')
			
			if res == 0:
				raise ValueError("invalid thread id")
			elif res != 1:
				# """if it returns a number greater than one, you're in trouble, 
				# and you should call it again with exc=NULL to revert the effect"""
				ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
				raise SystemError("PyThreadState_SetAsyncExc failed")

		# 强行结束进程
		_async_raise(self.ident, SystemExit)
		# 关闭socket
		self.socketObj.close()

	def send(self, data):
		if self.socketObj:
			self.socketObj.sendto(data.encode(), self.remoteAddress)

	def remoteCall(self, funName, paramDict):
		codeDic = {'f':funName, 'p':paramDict}
		codeStr = JSONEncoder().encode(codeDic)
		self.send(codeStr)

	def goToPage(self, param):
		print('go to page', param)
		import sublime
		window = sublime.active_window()
		if window:
			window.open_file('%s:%s:%s'% (param[0], param[1], param[2]+1), sublime.ENCODED_POSITION)

if __name__ == "__main__":
	add1 = ('127.0.0.1', 12345)
	add2 = ('127.0.0.1', 12346)

	t1 = SocketThread(add1, add2)
	t2 = SocketThread(add2, add1)
	t1.start()
	t2.start()

	time.sleep(1)
	#t1.send('1 -> 2')
	#t2.send('2 -> 1')
	t1.remoteCall('fun',{'p1':1})