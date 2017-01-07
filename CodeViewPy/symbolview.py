# -*- coding: utf-8 -*-
from PyQt4 import QtGui,QtCore,uic,QtOpenGL
import time
import math
import SymbolScene
from db.SymbolAttr import SymbolAttr

class SymbolView(QtGui.QGraphicsView):
	def __init__(self, *args):
		super(SymbolView, self).__init__(*args)
		from UIManager import UIManager
		self.setScene(UIManager.instance().getSymbolScene())


		self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
		self.setCacheMode(QtGui.QGraphicsView.CacheNone)
		#self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
		self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
		self.setMouseTracking(True)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setAcceptDrops(True)
		self.setViewport(QtOpenGL.QGLWidget())

		self.centerPnt = QtCore.QPointF()
		self.scale(0.6,0.6)

		self.mousePressPnt = None
		self.mouseCurPnt = None
		self.isFrameSelectMode = False

	def mousePressEvent(self, event):
		self.mouseCurPnt = self.mousePressPnt = event.pos()

		item = self.itemAt(self.mousePressPnt)
		self.isFrameSelectMode = (not item)
		super(SymbolView, self).mousePressEvent(event)

	def mouseMoveEvent(self, event):
		if self.isFrameSelectMode:
			self.mouseCurPnt = event.pos()

		super(SymbolView,self).mouseMoveEvent(event)
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

		super(SymbolView, self).mouseReleaseEvent(event)

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
		super(SymbolView, self).drawForeground(painter, rectF)
		if self.isFrameSelectMode and self.mousePressPnt and self.mouseCurPnt:
			topLeftX = min(self.mousePressPnt.x(), self.mouseCurPnt.x())
			topLeftY = min(self.mousePressPnt.y(), self.mouseCurPnt.y())
			width = abs(self.mousePressPnt.x()-self.mouseCurPnt.x())
			height= abs(self.mousePressPnt.y()-self.mouseCurPnt.y())

			painter.setPen(QtGui.QPen(QtGui.QColor(100,164,230),1.0))
			painter.setBrush(QtGui.QBrush(QtGui.QColor(100,164,230,100)))
			painter.setTransform(QtGui.QTransform())
			painter.drawRect(topLeftX, topLeftY, width, height)


		painter.setTransform(QtGui.QTransform())
		painter.setFont(QtGui.QFont('tahoma', 8))
		from db.SymbolAttr import UIAttr

		lod = QtGui.QStyleOptionGraphicsItem().levelOfDetailFromTransform(self.transform())
		scene = self.scene()
		for uname, item in scene.symbolDict.items():
			uiAttr = item.getAttr(UIAttr.ATTR_UI)
			uiItem = uiAttr.uiItem
			arcLength = uiItem.radius[0] * (uiItem.theta[1] - uiItem.theta[0])
			if arcLength * lod > 15:
				posView = self.mapFromScene(uiItem.txtPos)
				painter.drawText(posView, item.name)

	def drawBackground(self, painter, rectF):
		trans = painter.worldTransform()
		lod = QtGui.QStyleOptionGraphicsItem().levelOfDetailFromTransform(trans)

		scene = self.scene()
		scene.updateNodeVisibility(lod)

		super(SymbolView, self).drawBackground(painter, rectF)
		lineList = scene.getLowPosList()

		t0 = time.clock()
		lineList = scene.getNormalPosList()
		for line in lineList:
			line.paint(painter,20,1.0)

		lineList = scene.getHighPosList()
		for line in lineList:
			line.paint(painter,100,2.0)


		t1 = time.clock()

