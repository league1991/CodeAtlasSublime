# -*- coding: utf-8 -*-
from PyQt4 import QtGui,QtCore
import math
import codescene
import ui.CodeUIItem as CodeUIItem


class CodeView(QtGui.QGraphicsView):
	def __init__(self, *args):
		super(CodeView, self).__init__(*args)
		from UIManager import UIManager
		self.setScene(UIManager.instance().getScene())
		#self.setInteractive(True)
		self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
		self.setCacheMode(QtGui.QGraphicsView.CacheNone)
		#self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
		self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
		self.setMouseTracking(True)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setAcceptDrops(True)

		self.mousePressPnt = None
		self.mouseCurPnt = None
		self.isFrameSelectMode = False
		self.isBrushSelectMode = False
		self.isBrushDeselectMode = False
		self.isMousePressed = False
 
		self.updateTimer = QtCore.QTimer()
		self.updateTimer.setInterval(70)
		#print('connect')
		self.connect(self.updateTimer, QtCore.SIGNAL('timeout()'), self, QtCore.SLOT('updateView()'))
		#print('connect end')
		#self.updateTimer.start()
		self.centerPnt = QtCore.QPointF()
		self.scale(0.6,0.6)
		self.brushRadius = 8
		self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(50,50,50)))

	@QtCore.pyqtSlot()
	def updateView(self):
		print('update view begin ')
		scene = self.scene()
		if scene:
			#print('update view')
			scene.acquireLock()

			pos = scene.getSelectedCenter()
			self.centerPnt = self.centerPnt * 0.97 + pos * 0.03
			self.centerOn(self.centerPnt) 
			scene.releaseLock()
			#self.viewport().update()
		#print('update view end ')

	def keyPressEvent(self, event):
		self.setCursor(QtCore.Qt.ArrowCursor)
		if event.modifiers() == QtCore.Qt.AltModifier:
			from UIManager import UIManager
			mainUI = UIManager.instance().getMainUI()
			if event.key() == QtCore.Qt.Key_Up:
				mainUI.goToUp()
			elif event.key() == QtCore.Qt.Key_Down:
				mainUI.goToDown()
			elif event.key() == QtCore.Qt.Key_Left:
				mainUI.goToLeft()
			elif event.key() == QtCore.Qt.Key_Right:
				mainUI.goToRight()
			elif event.key() == QtCore.Qt.Key_1:
				mainUI.showScheme([1])
			elif event.key() == QtCore.Qt.Key_2:
				mainUI.showScheme([2])
			elif event.key() == QtCore.Qt.Key_3:
				mainUI.showScheme([3])
			elif event.key() == QtCore.Qt.Key_4:
				mainUI.showScheme([4])
			elif event.key() == QtCore.Qt.Key_5:
				mainUI.showScheme([5])
			elif event.key() == QtCore.Qt.Key_6:
				mainUI.showScheme([6])
			elif event.key() == QtCore.Qt.Key_7:
				mainUI.showScheme([7])
			elif event.key() == QtCore.Qt.Key_8:
				mainUI.showScheme([8])
			elif event.key() == QtCore.Qt.Key_9:
				mainUI.showScheme([9])
		elif event.key() == QtCore.Qt.Key_Control:
			#print('ctrl pressed')
			self.isBrushSelectMode = True
			self.setCursor(QtCore.Qt.BlankCursor)
		elif event.key() == QtCore.Qt.Key_Shift:
			self.isBrushDeselectMode = True
			self.setCursor(QtCore.Qt.BlankCursor)
		else:
			super(CodeView, self).keyPressEvent(event)

	def keyReleaseEvent(self, event):
		self.setCursor(QtCore.Qt.ArrowCursor)
		if event.key() == QtCore.Qt.Key_Control:
			self.isBrushSelectMode = False
			#print('ctrl release')
		elif event.key() == QtCore.Qt.Key_Shift:
			self.isBrushDeselectMode = False
		else:
			super(CodeView, self).keyReleaseEvent(event)

	def mousePressEvent(self, event):
		self.mouseCurPnt = self.mousePressPnt = event.pos()
		self.isMousePressed = True
		item = self.itemAt(self.mousePressPnt)
		self.isFrameSelectMode = (not item) and (not self.isBrushSelectMode) and (not self.isBrushDeselectMode)
		#print('is frame select', self.isFrameSelectMode)
		# if item:
		# 	item.mousePressEvent(event)
		if not self.isBrushSelectMode and not self.isBrushDeselectMode:
			super(CodeView, self).mousePressEvent(event)

	def mouseMoveEvent(self, event):
		#print('mouse move begin ')
		if self.isFrameSelectMode:
			#print('frame move')
			self.mouseCurPnt = event.pos()
		elif self.isBrushSelectMode or self.isBrushDeselectMode:
			self.mouseCurPnt = event.pos()
			if self.isMousePressed:
				x = event.pos().x()
				y = event.pos().y()
				itemList = self.items(x-self.brushRadius, y-self.brushRadius, self.brushRadius*2, self.brushRadius*2)
				for item in itemList:
					item.setSelected(self.isBrushSelectMode)
		super(CodeView,self).mouseMoveEvent(event)
		#self.invalidateScene(self.scene().sceneRect())
		#self.update()
		self.viewport().update()
		#print('mouse move end ')

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

			self.scene().clearSelection()
			for item in itemList:
				item.setSelected(True)

		super(CodeView, self).mouseReleaseEvent(event)

	def wheelEvent(self, event):
		#print('wheel begin ')
		posScene = self.mapToScene(event.pos())
		factor = 1.001 ** event.delta()
		self.scale(factor, factor)

		posMouse = self.mapFromScene(posScene)
		mov = posMouse - event.pos()
		self.horizontalScrollBar().setValue(mov.x() + self.horizontalScrollBar().value())
		self.verticalScrollBar().setValue(mov.x() + self.verticalScrollBar().value())

		self.centerPnt = self.mapToScene(self.viewport().rect().center())
		#print('wheel end ')

	def drawForeground(self, painter, rectF):
		#print('draw foregrpund begin ')
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
		elif self.isBrushSelectMode and self.mouseCurPnt:
			painter.setPen(QtGui.QPen(QtGui.QColor(100,164,230),1.0))
			painter.setBrush(QtGui.QBrush(QtGui.QColor(100,164,230,100)))
			painter.setTransform(QtGui.QTransform())
			x = self.mouseCurPnt.x()
			y = self.mouseCurPnt.y()
			painter.drawEllipse(x-self.brushRadius, y-self.brushRadius, self.brushRadius*2, self.brushRadius*2)
		elif self.isBrushDeselectMode and self.mouseCurPnt:
			painter.setPen(QtGui.QPen(QtGui.QColor(242,98,101),1.0))
			painter.setBrush(QtGui.QBrush(QtGui.QColor(242,98,101,100)))
			painter.setTransform(QtGui.QTransform())
			x = self.mouseCurPnt.x()
			y = self.mouseCurPnt.y()
			painter.drawEllipse(x-self.brushRadius, y-self.brushRadius, self.brushRadius*2, self.brushRadius*2)

		self.drawScheme(painter, rectF)
		self.drawLegend(painter, rectF)
		#print('draw foregrpund end')
		#return True

	def drawScheme(self, painter, rectF):
		painter.setTransform(QtGui.QTransform())
		painter.setFont(QtGui.QFont('tahoma', 8))
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		schemeList = scene.getCurrentSchemeList()
		#print('schemelist', schemeList)
		cw = 10
		y  = 10
		for ithScheme, schemeName in enumerate(schemeList):
			painter.setPen(QtCore.Qt.NoPen)
			painter.setBrush(QtGui.QBrush(QtGui.QColor(200,200,200,100)))
			painter.drawRect(QtCore.QRect(10,y,40,cw+1))

			painter.setPen(QtCore.Qt.white)
			painter.drawText(14, y+cw, 'Alt + %s   %s' % (ithScheme+1, schemeName))
			y += cw + 2


	def drawLegend(self, painter, rectF):
		painter.setTransform(QtGui.QTransform())
		painter.setFont(QtGui.QFont('tahoma', 8))

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

		cw = 10
		y = self.height() - 20
		for cname, clr in classNameDict.items():
			painter.setPen(QtCore.Qt.NoPen)
			painter.setBrush(QtGui.QBrush(clr))
			painter.drawRect(QtCore.QRect(10,y,cw,cw))

			painter.setPen(QtCore.Qt.white)
			painter.drawText(cw+12, y+cw, cname)
			y -= cw + 2


	def paintEvent(self, QPaintEvent):
		#print('paint event begin ')
		scene = self.scene()
		scene.acquireLock()
		QtGui.QGraphicsView.paintEvent(self, QPaintEvent)
		scene.releaseLock()
		#print('paint event end ')