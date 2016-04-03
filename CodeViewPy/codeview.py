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
 
		self.updateTimer = QtCore.QTimer()
		self.updateTimer.setInterval(70)
		#print('connect')
		self.connect(self.updateTimer, QtCore.SIGNAL('timeout()'), self, QtCore.SLOT('updateView()'))
		#print('connect end')
		#self.updateTimer.start()
		self.centerPnt = QtCore.QPointF()
		self.scale(0.7,0.7)

	@QtCore.pyqtSlot()
	def updateView(self):
		scene = self.scene()
		if scene:
			#print('update view')
			scene.acquireLock()

			pos = scene.getSelectedCenter()
			self.centerPnt = self.centerPnt * 0.97 + pos * 0.03
			self.centerOn(self.centerPnt) 
			scene.releaseLock()
			#self.viewport().update()

	def keyPressEvent(self, event):
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

		else:
			super(CodeView, self).keyPressEvent(event)

	def mousePressEvent(self, event):
		self.mouseCurPnt = self.mousePressPnt = event.pos()

		item = self.itemAt(self.mousePressPnt)
		self.isFrameSelectMode = (not item)
		#print('is frame select', self.isFrameSelectMode)
		super(CodeView, self).mousePressEvent(event)

	def mouseMoveEvent(self, event):
		if self.isFrameSelectMode:
			#print('frame move')
			self.mouseCurPnt = event.pos()

		super(CodeView,self).mouseMoveEvent(event)
		#self.invalidateScene(self.scene().sceneRect())
		#self.update()
		self.viewport().update()

	def mouseReleaseEvent(self, event):
		self.mouseCurPnt = event.pos()
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
		if self.isFrameSelectMode and self.mousePressPnt and self.mouseCurPnt:
			topLeftX = min(self.mousePressPnt.x(), self.mouseCurPnt.x())
			topLeftY = min(self.mousePressPnt.y(), self.mouseCurPnt.y())
			width = abs(self.mousePressPnt.x()-self.mouseCurPnt.x())
			height= abs(self.mousePressPnt.y()-self.mouseCurPnt.y())

			painter.setPen(QtGui.QPen(QtGui.QColor(100,164,230),1.0))
			painter.setBrush(QtGui.QBrush(QtGui.QColor(100,164,230,100)))
			painter.setTransform(QtGui.QTransform())
			painter.drawRect(topLeftX, topLeftY, width, height)

		#return True

	def paintEvent(self, QPaintEvent):
		scene = self.scene()
		scene.acquireLock()
		QtGui.QGraphicsView.paintEvent(self, QPaintEvent)
		scene.releaseLock()