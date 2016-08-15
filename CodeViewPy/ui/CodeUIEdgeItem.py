from PyQt4 import QtCore, QtGui, uic
import math

class CodeUIEdgeItem(QtGui.QGraphicsItem):
	def __init__(self, srcUniqueName, tarUniqueName, dbRef = None, parent = None, scene = None):
		super(CodeUIEdgeItem, self).__init__(parent, scene)
		#self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
		self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
		self.setAcceptHoverEvents(True)
		#self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable)
		self.srcUniqueName = srcUniqueName
		self.tarUniqueName = tarUniqueName
		self.setZValue(-1)
		self.path = None
		self.pathShape = None
		self.curve = None
		self.pathPnt = None

		self.file = ''
		self.line = -1
		self.column = -1
		if dbRef:
			self.file = dbRef.file().longname()
			self.line = dbRef.line()
			self.column = dbRef.column()

		self.isHover = False

		# (number, point)
		self.orderData = None
		self.buildPath()
		self.isConnectedToFocusNode = False
		self.schemeColorList = []

	def getNodePos(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		srcNode = scene.getNode(self.srcUniqueName)
		tarNode = scene.getNode(self.tarUniqueName)
		if not srcNode or not tarNode:
			return QtCore.QPointF(), QtCore.QPointF()
		srcPos = srcNode.pos()
		tarPos = tarNode.pos()
		#sign = 1 if tarPos.x() > srcPos.x() else -1
		return (srcNode.getRightSlotPos(), tarNode.getLeftSlotPos())
		# if tarPos.x() > srcPos.x():
		# 	return (srcNode.getRightSlotPos(), tarNode.getLeftSlotPos())
		# else:
		# 	return (srcNode.getLeftSlotPos(), tarNode.getRightSlotPos())

	def getNodeCenterPos(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		srcNode = scene.getNode(self.srcUniqueName)
		tarNode = scene.getNode(self.tarUniqueName)
		if not srcNode or not tarNode:
			return QtCore.QPointF(), QtCore.QPointF()
		return srcNode.pos(), tarNode.pos()

	def getMiddlePos(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		srcNode = scene.getNode(self.srcUniqueName)
		tarNode = scene.getNode(self.tarUniqueName)
		if not srcNode or not tarNode:
			return QtCore.QPointF()
		return (srcNode.pos() + tarNode.pos()) * 0.5

	def boundingRect(self):
		srcPos, tarPos = self.getNodePos()
		#print(srcPos, tarPos)
		minPnt = (min(srcPos.x(), tarPos.x()), min(srcPos.y(), tarPos.y()))
		maxPnt = (max(srcPos.x(), tarPos.x()), max(srcPos.y(), tarPos.y()))

		return QtCore.QRectF(minPnt[0], minPnt[1], maxPnt[0]-minPnt[0], maxPnt[1]- minPnt[1])

	def getNumberRect(self):
		if self.orderData:
			pnt = self.orderData[1]
			rect = QtCore.QRectF(pnt.x()-10, pnt.y()-10,20,20)
			return rect
		return QtCore.QRectF()

	def buildPath(self):
		srcPos, tarPos = self.getNodePos()
		if self.pathPnt and (self.pathPnt[0]-srcPos).manhattanLength() < 0.05 and (self.pathPnt[1]-tarPos).manhattanLength() < 0.05:
			return self.path 
		#print('build path', self.pathPnt, srcPos, tarPos)
		self.pathPnt = (srcPos, tarPos)
		path = QtGui.QPainterPath()  
		path.moveTo(srcPos)
		dx = tarPos.x() - srcPos.x()
		p1 = srcPos + QtCore.QPointF(dx*0.3, 0)
		p2 = tarPos + QtCore.QPointF(-dx*0.7, 0)
		path.cubicTo(p1,p2,tarPos)
		self.curve = QtGui.QPainterPath(path)
		self.path = path

		from PyQt4.QtGui import QPainterPathStroker
		stroker = QPainterPathStroker()
		stroker.setWidth(10.0)
		self.pathShape = stroker.createStroke(self.path)
		return path

	def findCurveYPos(self, x):
		if not self.pathPnt:
			return 0.0
		if not self.curve:
			minY = min(self.pathPnt[0].y(), self.pathPnt[1].y())
			maxY = max(self.pathPnt[0].y(), self.pathPnt[1].y())
			return (minY + maxY) * 0.5
		sign = 1.0 if self.pathPnt[1].x() > self.pathPnt[0].x() else -1.0
		minT = 0.0
		maxT = 1.0
		minPnt = self.curve.pointAtPercent(minT)
		maxPnt = self.curve.pointAtPercent(maxT)
		for i in range(8):
			midT = (minT + maxT) * 0.5
			midPnt = self.curve.pointAtPercent(midT)
			if (midPnt.x() - x) * sign < 0:
				minT = midT
				minPnt = midPnt
			else:
				maxT = midT
				maxPnt = midPnt
		return (minPnt.y() + maxPnt.y()) * 0.5

	def shape(self):
		#srcPos, tarPos = self.getNodePos()
		#path = QtGui.QPainterPath()
		# path.moveTo(srcPos)
		# path.lineTo(tarPos)
		#path.addRect(self.boundingRect())
		#return path
		path = QtGui.QPainterPath(self.pathShape)
		if self.orderData:
			pnt = self.orderData[1]
			rect = self.getNumberRect()
			path.addEllipse(rect)
		return path

	def paint(self, painter, styleOptionGraphicsItem, widget_widget=None):
		painter.setRenderHint(QtGui.QPainter.Antialiasing)
		clr = QtCore.Qt.darkGray if self.isSelected() else QtCore.Qt.lightGray

		srcPos, tarPos = self.getNodeCenterPos()
		isReverse = srcPos.x() > tarPos.x()
		isHighLight = False
		if self.isSelected() or self.isHover:
			clr = QtGui.QColor(255,255,0)
			isHighLight = True
		# elif self.isConnectedToFocusNode:
		# 	clr = QtGui.QColor(200,200,200,255)
		else:
			if isReverse:
				clr = QtGui.QColor(159,49,52,200)
			else:
				clr = QtGui.QColor(150,150,150,180)
			#clr = QtGui.QColor(230,230,230,255)

		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		# srcNode = scene.getNode(self.srcUniqueName)
		# tarNode = scene.getNode(self.tarUniqueName)
		penStyle = QtCore.Qt.SolidLine
		penWidth = 3.0
		# if srcNode and tarNode and srcNode.isFunction() and tarNode.isFunction():
		# 	pass
		# else:
		# 	penStyle = QtCore.Qt.DotLine
		pen = QtGui.QPen(clr, penWidth, penStyle)

		# srcPos, tarPos = self.getNodePos()
		# #midPos = (srcPos + tarPos) * 0.5
		# midPos = tarPos
		# #d = [tarPos.x() - srcPos.x(), tarPos.y() - srcPos.y()]
		# d = [tarPos.x() - srcPos.x(), 0]
		# dirLength = math.sqrt(d[0]*d[0] + d[1]*d[1])
		# d[0] /= (dirLength + 1e-5)
		# d[1] /= (dirLength + 1e-5)

		# ld = (-d[1],d[0])
		# back = -10
		# side = 4
		# leftPos  = QtCore.QPointF(midPos.x() + d[0]*back + ld[0]*side, midPos.y() + d[1]*back + ld[1]*side)
		# rightPos = QtCore.QPointF(midPos.x() + d[0]*back + ld[0]*-side, midPos.y() + d[1]*back + ld[1]*-side)

		#painter.drawLines([srcPos, tarPos, leftPos, midPos, rightPos, midPos])
		#painter.drawLines([leftPos, midPos, rightPos, midPos])
		if self.schemeColorList:
			if isHighLight:
				pen.setWidthF(9.0)
				painter.setPen(pen)
				painter.drawPath(self.path)
			dash = 5
			pen = QtGui.QPen(clr, 3.0, QtCore.Qt.CustomDashLine, QtCore.Qt.FlatCap)
			pen.setDashPattern([dash, dash*(len(self.schemeColorList)-1)])
			for i, schemeColor in enumerate(self.schemeColorList):
				pen.setDashOffset(i*dash)
				pen.setColor(schemeColor)
				painter.setPen(pen)
				painter.drawPath(self.path)
		else:
			if isHighLight:
				pen.setWidthF(9.0)
			painter.setPen(pen)
			painter.drawPath(self.path)

		if self.orderData is not None:
			#print('order data', self.orderData)
			#print('target pnt ', tarPos)
			order = self.orderData[0]
			rect = self.getNumberRect()
			painter.setBrush(clr)
			painter.setPen(QtCore.Qt.NoPen)
			painter.drawEllipse(rect)
			#painter.drawRect(rect)
			painter.setPen(QtGui.QPen(QtGui.QColor(0,0,0), 2.0))

			textFont = QtGui.QFont('tahoma', 12)
			painter.setFont(textFont)
			painter.drawText(rect, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter, '%s' % order)

	def hoverLeaveEvent(self, QGraphicsSceneHoverEvent):
		super(CodeUIEdgeItem, self).hoverLeaveEvent(QGraphicsSceneHoverEvent)
		self.isHover = False

	def hoverEnterEvent(self, QGraphicsSceneHoverEvent):
		super(CodeUIEdgeItem, self).hoverEnterEvent(QGraphicsSceneHoverEvent)
		self.isHover = True

	def mouseDoubleClickEvent(self, event):
		super(CodeUIEdgeItem, self).mouseDoubleClickEvent(event)

		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.showInEditor()