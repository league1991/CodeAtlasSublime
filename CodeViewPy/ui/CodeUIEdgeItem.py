from PyQt4 import QtCore, QtGui, uic
import math

class CodeUIEdgeItem(QtGui.QGraphicsItem):
	def __init__(self, srcUniqueName, tarUniqueName, parent = None, scene = None):
		super(CodeUIEdgeItem, self).__init__(parent, scene)
		#self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
		#self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
		#self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable)
		self.srcUniqueName = srcUniqueName
		self.tarUniqueName = tarUniqueName
		self.setZValue(-1)

	def getNodePos(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		srcNode = scene.getNode(self.srcUniqueName)
		tarNode = scene.getNode(self.tarUniqueName)
		if not srcNode or not tarNode:
			return QtCore.QPointF(), QtCore.QPointF()
		return srcNode.pos(), tarNode.pos()

	def boundingRect(self):
		srcPos, tarPos = self.getNodePos()
		#print(srcPos, tarPos)
		minPnt = (min(srcPos.x(), tarPos.x()), min(srcPos.y(), tarPos.y()))
		maxPnt = (max(srcPos.x(), tarPos.x()), max(srcPos.y(), tarPos.y()))

		return QtCore.QRectF(minPnt[0], minPnt[1], maxPnt[0]-minPnt[0], maxPnt[1]- minPnt[1])

	def shape(self):
		srcPos, tarPos = self.getNodePos()
		path = QtGui.QPainterPath()
		# path.moveTo(srcPos)
		# path.lineTo(tarPos)
		path.addRect(self.boundingRect())
		return path

	def paint(self, painter, styleOptionGraphicsItem, widget_widget=None):
		painter.setRenderHint(QtGui.QPainter.Antialiasing)
		srcPos, tarPos = self.getNodePos()
		clr = QtCore.Qt.darkGray if self.isSelected() else QtCore.Qt.lightGray
		painter.setPen(QtGui.QPen(QtGui.QColor(128,128,128), 2.0))

		midPos = (srcPos + tarPos) * 0.5
		d = [tarPos.x() - srcPos.x(), tarPos.y() - srcPos.y()]
		dirLength = math.sqrt(d[0]*d[0] + d[1]*d[1])
		d[0] /= (dirLength + 1e-5)
		d[1] /= (dirLength + 1e-5)

		ld = (-d[1],d[0])
		leftPos  = QtCore.QPointF(midPos.x() + d[0]*-5 + ld[0]*2, midPos.y() + d[1]*-5 + ld[1]*2)
		rightPos = QtCore.QPointF(midPos.x() + d[0]*-5 + ld[0]*-2, midPos.y() + d[1]*-5 + ld[1]*-2)

		painter.drawLines([srcPos, tarPos, leftPos, midPos, rightPos, midPos])