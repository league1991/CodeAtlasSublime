# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, uic, QtWidgets
import math

class SymbolUIItem(QtWidgets.QGraphicsItem):
	COLOR_DICT = {}
	def __init__(self, node, parent = None, scene = None):
		super(SymbolUIItem, self).__init__(parent, scene)
		isIgnore = node and node.getKind() == node.KIND_UNKNOWN
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, not isIgnore)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, not isIgnore)
		self.setAcceptDrops(True);
		self.setAcceptHoverEvents(True)
		self.node = node
		self.path = None
		self.rect = None
		self.isHover = False
		self.theta = (0,0)
		self.radius= (0,0)
		self.txtRadius = 0
		self.setToolTip("%s:%s" % (node.name, node.getKindName()))
		self.txtPos = None

		if not SymbolUIItem.COLOR_DICT:
			SymbolUIItem.COLOR_DICT = \
				{self.node.KIND_FUNCTION: QtGui.QColor(190,228,73),
				 self.node.KIND_VARIABLE: QtGui.QColor(255,198,217),
				 self.node.KIND_CLASS:    QtGui.QColor(154,177,209),
				 self.node.KIND_NAMESPACE: QtGui.QColor(154,225,209),
				 self.node.KIND_UNKNOWN: QtGui.QColor(195,195,195),
				 }

		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable)

	def getNode(self):
		return self.node

	def hoverEnterEvent(self, QGraphicsSceneHoverEvent):
		super(SymbolUIItem, self).hoverEnterEvent(QGraphicsSceneHoverEvent)
		self.isHover = True

	def hoverLeaveEvent(self, QGraphicsSceneHoverEvent):
		super(SymbolUIItem, self).hoverLeaveEvent(QGraphicsSceneHoverEvent)
		self.isHover = False

	def getCurveSlot(self):
		return self.polar2Coord(self.radius[0], (self.theta[0] + self.theta[1])*0.5)

	def contextMenuEvent(self, event):
		from UIManager import UIManager

		itemMenu = UIManager.instance().getMainUI().getSymbolMenu()
		itemMenu.exec(event.screenPos())

	def buildUI(self, uiAttr, scene):
		self.prepareGeometryChange()
		self.path = QtGui.QPainterPath()

		maxA = uiAttr.maxTheta
		minA = uiAttr.minTheta
		minR = scene.getBaseRadius()
		maxR = uiAttr.maxR
		self.txtRadius = uiAttr.minR
		self.theta = (minA, maxA)
		self.radius= (minR, maxR)
		begDir = (math.cos(minA), -math.sin(minA))
		endDir = (math.cos(maxA), -math.sin(maxA))

		width = maxR*2
		self.path.moveTo(maxR * begDir[0], maxR * begDir[1])
		self.path.arcTo(-maxR, -maxR, width, width, math.degrees(minA), math.degrees(maxA-minA))
		#self.rect = QtCore.QRectF(-maxR, -maxR, width, width)

		rect = QtCore.QRectF(1e6,1e6,-2e6,-2e6)
		self._addRectPnt(rect, minR * begDir[0], minR * begDir[1])
		self._addRectPnt(rect, minR * endDir[0], minR * endDir[1])
		angle = minA
		for i in range(7):
			x, y = maxR*math.cos(angle)*1.2, maxR*math.sin(angle)*-1.2
			angle += (maxA - minA)/7
			self._addRectPnt(rect, x, y)
		self.rect = rect

		width = minR*2
		self.path.arcTo(-minR, -minR, width, width, math.degrees(maxA), math.degrees(minA-maxA))
		self.path.closeSubpath()

		self.txtPos = self.polar2Coord(0.5*(self.radius[0] + self.radius[1]), 0.5*(self.theta[0]+ self.theta[1]))
		self.txtPos = QtCore.QPointF(self.txtPos[0], self.txtPos[1])

	def polar2Coord(self, r, theta):
		return r * math.cos(theta), -r * math.sin(theta)

	def _addRectPnt(self, rect, x, y):
		if x < rect.left():
			rect.setLeft(x)
		if x > rect.right():
			rect.setRight(x)
		if y < rect.top():
			rect.setTop(y)
		if y > rect.bottom():
			rect.setBottom(y)

	def boundingRect(self):
		return self.rect

	def shape(self):
		return self.path

	def getMaxArcLength(self):
		return self.radius[1] * (self.theta[1] - self.theta[0])

	def updateVisible(self):
		al = self.radius[1] * (self.theta[1] - self.theta[0])
		self.setVisible(al > 5)

	def paint(self, painter, QStyleOptionGraphicsItem, QWidget_widget=None):
		trans = painter.worldTransform()
		lod = QtWidgets.QStyleOptionGraphicsItem().levelOfDetailFromTransform(trans)

		midR = (self.radius[0] + self.radius[1]) * 0.5
		arcLength = midR * (self.theta[1] - self.theta[0])
		arcWidth  = self.radius[1] - self.radius[0]
		# if min(arcLength, arcWidth) * lod < 2:
		# 	return

		midTheta = (self.theta[0] + self.theta[1]) * 0.5
		color = self.COLOR_DICT[self.node.getKind()]

		selectedOrHover = self.isSelected() or self.isHover
		if selectedOrHover:
			color = color.darker(130)

		painter.setBrush(color)

		if min(arcLength, arcWidth) * lod > 5:
			penColor = color.darker(130)
			painter.setPen(QtGui.QPen(penColor))
		else:
			painter.setPen(QtCore.Qt.NoPen)
		painter.drawPath(self.path)

		# painter.setBrush(QtCore.Qt.NoBrush)
		# painter.drawRect(self.rect)
		# if min(arcLength, arcWidth) * lod > 20:
		# 	#painter.rotate(30)
		# 	painter.rotate(math.degrees(-midTheta))
		# 	painter.setPen(QtGui.QPen(QtGui.QColor(30,30,30)))
		# 	fontSize = (arcWidth if arcLength > arcWidth else arcWidth) * 0.1
		# 	painter.setFont(QtGui.QFont('tahoma', fontSize))
		# 	painter.drawText(QtCore.QPointF(self.txtRadius ,0), self.node.name)