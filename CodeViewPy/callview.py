# -*- coding: utf-8 -*-
from PyQt5 import QtGui,QtCore,uic,QtOpenGL, QtWidgets
import time
import math
from symbolview import SymbolView
#import SymbolView as symbolview
from db.SymbolAttr import SymbolAttr

qtCreatorFile = './ui/Call.ui' # Enter file here.
Ui_CallView, QtBaseClass = uic.loadUiType(qtCreatorFile)

class CallView(QtWidgets.QScrollArea, Ui_CallView):
	def __init__(self, parent = None):
		QtWidgets.QScrollArea.__init__(self)
		Ui_CallView.__init__(self)
		self.setupUi(self)