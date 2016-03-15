import socket
import threading
import time
import inspect
import ctypes
from json import *

class SocketThread(threading.Thread):
	def __init__(self, myAddress, remoteAddress):
		threading.Thread.__init__(self)
		self.myAddress = myAddress
		self.remoteAddress = remoteAddress
		self.socketObj = None

	def isListening(self):
		return self.socketObj is not None

	def run(self):
		from UIManager import UIManager
		print('run', self.name)
		address = self.myAddress
		self.socketObj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socketObj.bind(address)

		while True:
			data, addr = self.socketObj.recvfrom(1024 * 5)
			print('recv data, addr')
			dataStr = data.decode()
			print('data str')
			dataObj = JSONDecoder().decode(dataStr)
			print('data obj')

			funName = dataObj.get('f')
			paramDict = dataObj.get('p', None)
			print('----------receive:', funName, paramDict)
			#funObj = self.registerCb.get(funName, None)
			mainUI = UIManager.instance().getMainUI()
			print('main ui:', mainUI)
			funObj = getattr(mainUI, funName)
			print('fun obj:', funObj)
			if funObj:
				if paramDict is None:
					funObj()
				else:
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