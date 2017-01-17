# -*- coding: utf-8 -*-
import socket
import threading
import time
import inspect
import ctypes
from json import *
from PyQt4 import QtCore, Qt

class SocketThread(QtCore.QThread):
#class SocketThread(threading.Thread):
	recvSignal = QtCore.pyqtSignal(str)
	def __init__(self, myAddress, remoteAddress):
		# threading.Thread.__init__(self)
		super(SocketThread, self).__init__()
		self.myAddress = myAddress
		self.remoteAddress = remoteAddress
		self.socketObj = None

	def isListening(self):
		return self.socketObj is not None

	def run(self):
		from UIManager import UIManager
		mainUI = UIManager.instance().getMainUI()
		self.recvSignal.connect(mainUI.onSocketEvent, Qt.Qt.QueuedConnection)

		address = self.myAddress
		self.socketObj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socketObj.bind(address)

		while True:
			data, addr = self.socketObj.recvfrom(1024 * 5)
			dataStr = data.decode()
			self.recvSignal.emit(dataStr)

		print ('close socket')
		self.socketObj.close()

	def stop(self):
		def _async_raise(tid, exctype):
			"""raises the exception, performs cleanup if needed"""
			if not inspect.isclass(exctype):
				exctype = type(exctype)
			res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))

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
			encodedData = data.encode()
			self.socketObj.sendto(encodedData, self.remoteAddress)

	def remoteCall(self, funName, paramDict):
		codeDic = {'f':funName, 'p':paramDict}
		codeStr = JSONEncoder().encode(codeDic)
		#codeStr = 'aaa'
		self.send(codeStr)

if __name__ == "__main__":
	add1 = ('127.0.0.1', 12345)
	add2 = ('127.0.0.1', 12346)

	t1 = SocketThread(add1, add2)
	#t2 = SocketThread(add2, add1)
	t1.start()
	#t1.send("abc")
	#t2.start()

	#t1.send('1 -> 2')
	#t2.send('2 -> 1')
	t1.remoteCall('onTest2', ['fff',123])
	time.sleep(100)