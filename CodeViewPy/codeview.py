# -*- coding: utf-8 -*-
from PyQt5 import QtGui,QtCore,QtWidgets
import math
import codescene
import time
import ui.CodeUIItem as CodeUIItem


class CodeView(QtWidgets.QGraphicsView):
	def __init__(self, *args):
		super(CodeView, self).__init__(*args)
		from UIManager import UIManager
		self.setScene(UIManager.instance().getScene())
		self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
		self.setCacheMode(QtWidgets.QGraphicsView.CacheNone)
		#self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
		self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		self.setMouseTracking(True)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setAcceptDrops(True)

		self.mousePressPnt = None
		self.mouseCurPnt = None
		self.isFrameSelectMode = False
		self.isMousePressed = False
 
		self.updateTimer = QtCore.QTimer()
		self.updateTimer.setInterval(70)
		# self.connect(self.updateTimer, QtCore.SIGNAL('timeout()'), self, QtCore.SLOT('updateView()'))
		self.updateTimer.timeout.connect(self.updateView)
		self.centerPnt = QtCore.QPointF()
		self.scale(0.6,0.6)
		self.brushRadius = 8
		self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(50,50,50)))
		self.hudFont = QtGui.QFont('tahoma', 8)
		self.hudFontMetric = QtGui.QFontMetrics(self.hudFont)

	@QtCore.pyqtSlot()
	def updateView(self):
		scene = self.scene()
		if scene:
			scene.acquireLock()
			pos = scene.getSelectedCenter()
			self.centerPnt = self.centerPnt * 0.97 + pos * 0.03
			self.centerOn(self.centerPnt) 
			scene.releaseLock()

	def keyPressEvent(self, event):
		from UIManager import UIManager
		mainUI = UIManager.instance().getMainUI()
		self.setCursor(QtCore.Qt.ArrowCursor)
		# if event.modifiers() == QtCore.Qt.AltModifier:
		if event.key() == QtCore.Qt.Key_Up:
			mainUI.goToUp()
		elif event.key() == QtCore.Qt.Key_Down:
			mainUI.goToDown()
		elif event.key() == QtCore.Qt.Key_Left:
			mainUI.goToLeft()
		elif event.key() == QtCore.Qt.Key_Right:
			mainUI.goToRight()
		elif event.modifiers() == QtCore.Qt.AltModifier:
			if event.key() == QtCore.Qt.Key_1:
				mainUI.showScheme([1, True])
			elif event.key() == QtCore.Qt.Key_2:
				mainUI.showScheme([2, True])
			elif event.key() == QtCore.Qt.Key_3:
				mainUI.showScheme([3, True])
			elif event.key() == QtCore.Qt.Key_4:
				mainUI.showScheme([4, True])
			elif event.key() == QtCore.Qt.Key_5:
				mainUI.showScheme([5, True])
			elif event.key() == QtCore.Qt.Key_6:
				mainUI.showScheme([6, True])
			elif event.key() == QtCore.Qt.Key_7:
				mainUI.showScheme([7, True])
			elif event.key() == QtCore.Qt.Key_8:
				mainUI.showScheme([8, True])
			elif event.key() == QtCore.Qt.Key_9:
				mainUI.showScheme([9, True])
		elif event.modifiers() == QtCore.Qt.ControlModifier:
			if event.key() == QtCore.Qt.Key_1:
				mainUI.toggleSelectedEdgeToScheme([1, True])
			elif event.key() == QtCore.Qt.Key_2:
				mainUI.toggleSelectedEdgeToScheme([2, True])
			elif event.key() == QtCore.Qt.Key_3:
				mainUI.toggleSelectedEdgeToScheme([3, True])
			elif event.key() == QtCore.Qt.Key_4:
				mainUI.toggleSelectedEdgeToScheme([4, True])
			elif event.key() == QtCore.Qt.Key_5:
				mainUI.toggleSelectedEdgeToScheme([5, True])
			elif event.key() == QtCore.Qt.Key_6:
				mainUI.toggleSelectedEdgeToScheme([6, True])
			elif event.key() == QtCore.Qt.Key_7:
				mainUI.toggleSelectedEdgeToScheme([7, True])
			elif event.key() == QtCore.Qt.Key_8:
				mainUI.toggleSelectedEdgeToScheme([8, True])
			elif event.key() == QtCore.Qt.Key_9:
				mainUI.toggleSelectedEdgeToScheme([9, True])
		else:
			super(CodeView, self).keyPressEvent(event)
		self.viewport().update()

	def keyReleaseEvent(self, event):
		self.setCursor(QtCore.Qt.ArrowCursor)
		if event.key() == QtCore.Qt.Key_Control or event.key() == QtCore.Qt.Key_Shift:
			pass
		else:
			super(CodeView, self).keyReleaseEvent(event)

	def mousePressEvent(self, event):
		self.mouseCurPnt = self.mousePressPnt = event.pos()
		self.isMousePressed = True
		item = self.itemAt(self.mousePressPnt)
		self.isFrameSelectMode = (not item)

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		if modifiers == QtCore.Qt.ControlModifier or modifiers == QtCore.Qt.ShiftModifier:
			if item:
				item.setSelected(not item.isSelected())
		else:
			super(CodeView, self).mousePressEvent(event)

	def mouseMoveEvent(self, event):
		self.mouseCurPnt = event.pos()
		if self.isFrameSelectMode:
			pass
		super(CodeView,self).mouseMoveEvent(event)
		#self.invalidateScene(self.scene().sceneRect())
		#self.update()
		self.viewport().update()

	def mouseReleaseEvent(self, event):
		self.mouseCurPnt = event.pos()
		self.isMousePressed = False
		if self.isFrameSelectMode:
			topLeftX = min(self.mousePressPnt.x(), self.mouseCurPnt.x())
			topLeftY = min(self.mousePressPnt.y(), self.mouseCurPnt.y())
			width = abs(self.mousePressPnt.x()-self.mouseCurPnt.x())
			height= abs(self.mousePressPnt.y()-self.mouseCurPnt.y())
			self.isFrameSelectMode = False
			itemList = self.items(topLeftX, topLeftY, width, height)

			modifiers = QtWidgets.QApplication.keyboardModifiers()
			if modifiers == QtCore.Qt.ShiftModifier:
				for item in itemList:
					item.setSelected(False)
			else:
				if modifiers != QtCore.Qt.ControlModifier:
					self.scene().clearSelection()
				for item in itemList:
					item.setSelected(True)

		super(CodeView, self).mouseReleaseEvent(event)

	def wheelEvent(self, event):
		posScene = self.mapToScene(event.pos())
		factor = 1.001 ** event.delta()
		self.scale(factor, factor)

		posMouse = self.mapFromScene(posScene)
		mov = posMouse - event.pos()
		self.horizontalScrollBar().setValue(mov.x() + self.horizontalScrollBar().value())
		self.verticalScrollBar().setValue(mov.x() + self.verticalScrollBar().value())

		self.centerPnt = self.mapToScene(self.viewport().rect().center())

	def drawForeground(self, painter, rectF):
		super(CodeView, self).drawForeground(painter, rectF)

		if self.isFrameSelectMode:
			if self.mousePressPnt and self.mouseCurPnt:
				topLeftX = min(self.mousePressPnt.x(), self.mouseCurPnt.x())
				topLeftY = min(self.mousePressPnt.y(), self.mouseCurPnt.y())
				width = abs(self.mousePressPnt.x()-self.mouseCurPnt.x())
				height= abs(self.mousePressPnt.y()-self.mouseCurPnt.y())

				painter.setPen(QtGui.QPen(QtGui.QColor(100,164,230),1.0))
				painter.setBrush(QtGui.QBrush(QtGui.QColor(100,164,230,100)))
				painter.setTransform(QtGui.QTransform())
				painter.drawRect(topLeftX, topLeftY, width, height)
		self.drawScheme(painter, rectF)
		self.drawLegend(painter, rectF)

	def drawScheme(self, painter, rectF):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		schemeList = scene.getCurrentSchemeList()
		nScheme = len(schemeList)
		if not nScheme:
			return
		painter.setTransform(QtGui.QTransform())
		painter.setFont(self.hudFont)
		colorList = scene.getCurrentSchemeColorList()
		cw = 10
		y  = 10

		maxWidth = 0
		for ithScheme, schemeName in enumerate(schemeList):
			schemeSize = self.hudFontMetric.size(QtCore.Qt.TextSingleLine, schemeName)
			maxWidth = max(maxWidth, schemeSize.width())

		painter.setCompositionMode(QtGui.QPainter.CompositionMode_Multiply)
		painter.setPen(QtCore.Qt.NoPen)
		painter.setBrush(QtGui.QColor(0,0,0,150))
		painter.drawRect(5,5, 80 + maxWidth, nScheme * cw + (nScheme-1)*2 + 10)

		painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
		for ithScheme, schemeName in enumerate(schemeList):
			painter.setPen(QtCore.Qt.NoPen)
			painter.setBrush(QtGui.QBrush(colorList[ithScheme]))
			painter.drawRect(QtCore.QRect(10,y+5,20,2))

			painter.setPen(QtGui.QPen(QtGui.QColor(255,157,38,255),1))
			painter.drawText(39, y+cw, 'Alt + %s' % (ithScheme+1,))
			painter.setPen(QtGui.QPen(QtGui.QColor(255,255,255,255),1))
			painter.drawText(QtCore.QRect(80,y-1,maxWidth,cw+3), QtCore.Qt.AlignRight | QtCore.Qt.AlignTop, schemeName)
			y += cw + 2

	def drawLegend(self, painter, rectF):
		painter.setTransform(QtGui.QTransform())
		painter.setFont(self.hudFont)

		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		itemDict = scene.getItemDict()
		classNameDict = {}
		for uname, item in itemDict.items():
			if item.isSelected() or item.isConnectedToFocusNode:
				cname = item.getClassName()
				if not cname:
					cname = '[global function]'
				classNameDict[cname] = item.getColor()

		maxWidth = 0
		cw = 10
		nClasses = len(classNameDict)
		if not nClasses:
			return

		for className in classNameDict.keys():
			classSize = self.hudFontMetric.size(QtCore.Qt.TextSingleLine, className)
			maxWidth = max(maxWidth, classSize.width())

		painter.setCompositionMode(QtGui.QPainter.CompositionMode_Multiply)
		painter.setPen(QtCore.Qt.NoPen)
		painter.setBrush(QtGui.QColor(0,0,0,150))
		interiorHeight = nClasses * cw + (nClasses-1)*2
		painter.drawRect(5,self.height()-15-interiorHeight, 22 + maxWidth, interiorHeight + 10)

		painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
		y = self.height() - 20
		for cname, clr in classNameDict.items():
			painter.setPen(QtCore.Qt.NoPen)
			painter.setBrush(QtGui.QBrush(clr))
			painter.drawRect(QtCore.QRect(10,y,cw,cw))

			painter.setPen(QtGui.QPen(QtGui.QColor(255,255,255,255),1))
			painter.drawText(cw+12, y+cw, cname)
			y -= cw + 2

	def drawComment(self, painter, rectF):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()

		for uname, itemData in scene.itemDataDict.items():
			item = scene.itemDict.get(uname, None)
			if not item:
				continue

	def paintEvent(self, QPaintEvent):
		scene = self.scene()
		scene.acquireLock()
		t0 = time.time()
		QtWidgets.QGraphicsView.paintEvent(self, QPaintEvent)
		scene.releaseLock()