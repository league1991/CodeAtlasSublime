# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
import math
import hashlib
import re

ITEM_UNKNOWN = 0
ITEM_VARIABLE = 1
ITEM_CLASS = 2
ITEM_FUNCTION = 3

def name2color(name):
	hashVal = int(hashlib.md5(name.encode("utf8")).hexdigest(),16) & 0xffffffff
	h = (hashVal & 0xff) / 255.0
	s = ((hashVal >> 8) & 0xff) / 255.0
	l = ((hashVal >> 16)& 0xff) / 255.0
	return QtGui.QColor.fromHslF(h, 0.35+s*0.3, 0.4+l*0.15)

def getFunctionColor(ent):
	defineList = ent.refs('definein')
	name = 'global'
	if not defineList:
		defineList = ent.refs('declarein')
	if defineList:
		ref = defineList[0]
		declareEnt = ref.ent()
		name = declareEnt.name()
	return name2color(name)

class CodeUIItem(QtGui.QGraphicsItem):
	def __init__(self, uniqueName, parent = None, scene = None):
		super(CodeUIItem, self).__init__(parent, scene)
		self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
		self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
		self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable)
		self.setAcceptDrops(True);
		self.setAcceptHoverEvents(True)
		self.uniqueName = uniqueName
		from db.DBManager import DBManager
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		entity = DBManager.instance().getDB().searchFromUniqueName(self.uniqueName)
		self.name = ''
		self.displayName = ''
		self.lines = 0
		self.kindName = ''
		self.kind = ITEM_UNKNOWN
		self.titleFont = QtGui.QFont('tahoma', 8)
		self.fontSize = QtCore.QSize()
		self.commentSize = QtCore.QSize()
		self.lineHeight = 0
		self.isConnectedToFocusNode = False
		if entity:
			self.setToolTip(entity.longname())
			self.name = entity.name()
			self.buildDisplayName(self.name)
			comment = scene.itemDataDict.get(self.uniqueName, {}).get('comment','')
			self.buildCommentSize(comment)
			self.kindName = entity.kindname()
			metricRes = entity.metric(('CountLine',))
			metricLine = metricRes.get('CountLine',1)
			if metricLine:
				self.lines = metricLine

		kindStr = self.kindName.lower()
		# 自定义数据
		self.customData = {}

		#print('kind str', kindStr)
		if kindStr.find('function') != -1 or kindStr.find('method') != -1:
			self.kind = ITEM_FUNCTION
			# 找出调用者和被调用者数目
			dbObj = DBManager.instance().getDB()
			callerList = dbObj.searchRefEntity(self.uniqueName, 'callby','function, method', True)[0]
			calleeList = dbObj.searchRefEntity(self.uniqueName, 'call','function, method', True)[0]
			self.customData['nCaller'] = len(callerList)
			self.customData['nCallee'] = len(calleeList)
			self.customData['callerR'] = self.getCallerRadius(len(callerList))
			self.customData['calleeR'] = self.getCallerRadius(len(calleeList))
		elif kindStr.find('attribute') != -1 or kindStr.find('variable') != -1 or kindStr.find('object') != -1:
			self.kind = ITEM_VARIABLE
			self.color = QtGui.QColor(255,198,217)
		elif kindStr.find('class') != -1 or kindStr.find('struct') != -1:
			self.kind = ITEM_CLASS
			self.color = QtGui.QColor(154,177,209)
		else:
			self.kind = ITEM_UNKNOWN
			self.color = QtGui.QColor(195,195,195)

		if self.kind == ITEM_FUNCTION or self.kind == ITEM_VARIABLE:
			if not entity:
				self.color = QtGui.QColor(190,228,73)
			else:
				defineList = entity.refs('definein')
				name = ''
				hasDefinition = True
				if not defineList:
					defineList = entity.refs('declarein')
					hasDefinition = False
				self.customData['hasDef'] = hasDefinition
				if defineList:
					ref = defineList[0]
					declareEnt = ref.ent()
					if declareEnt.kindname().lower().find('class') != -1 or \
						declareEnt.kindname().lower().find('struct') != -1:
						name = declareEnt.name()
						self.customData['className'] = name
					# self.setToolTip(declareEnt.kindname() + "+" + name)
				self.color = name2color(name)
		elif self.kind == ITEM_CLASS:
			self.color = name2color(self.name)

		self.displayScore = 0
		self.targetPos = self.pos()	# 用于动画目标
		self.isHover = False
		self.selectCounter = 0

	def getColor(self):
		return self.color

	def getClassName(self):
		if self.kind == ITEM_CLASS:
			return self.name
		return self.customData.get('className','')

	def buildDisplayName(self, name):
		p = re.compile(r'([A-Z]*[a-z0-9]*_*~*)')
		nameList = p.findall(name)
		#print('disp name list', nameList)
		partLength = 0
		self.displayName = ''
		fontMetrics = QtGui.QFontMetricsF(self.titleFont)
		for i, part in enumerate(nameList):
			self.displayName += part
			partLength += len(part)
			if partLength > 13:
				self.displayName += '\n'
				partLength = 0
		self.displayName = self.displayName.strip()
		nLine = self.displayName.count('\n')+1
		self.fontSize = fontMetrics.size(QtCore.Qt.TextSingleLine, self.name)
		self.lineHeight = fontMetrics.height()
		self.fontSize.setHeight((fontMetrics.lineSpacing()*nLine - fontMetrics.leading()))
		#print('disp name:\n', self.displayName,'---')

	def buildCommentSize(self, comment):
		if not comment:
			self.commentSize = QtCore.QSize()
			return

		fontMetrics = QtGui.QFontMetricsF(self.titleFont)
		lineHeight = fontMetrics.lineSpacing()
		width = fontMetrics.width(comment)
		lines = math.ceil(width/100)
		self.commentSize = QtCore.QSize(100, (fontMetrics.lineSpacing()*lines - fontMetrics.leading()))

	def isFunction(self):
		return self.kind == ITEM_FUNCTION

	def setTargetPos(self, pos):
		self.targetPos = pos

	def dispToTarget(self):
		return self.targetPos - self.pos()

	def moveToTarget(self, ratio):
		self.setPos(self.pos()* (1.0-ratio) + self.targetPos * ratio)

	def getKind(self):
		return self.kind

	def getUniqueName(self):
		return self.uniqueName

	def getEntity(self):
		from db.DBManager import DBManager
		return DBManager.instance().getDB().searchFromUniqueName(self.uniqueName)

	def getRadius(self):
		r = 8
		if self.kind != ITEM_VARIABLE:
			r = math.pow(float(self.lines+1), 0.3) * 5.0
		if self.isFunction():
			r = max(r, self.customData['callerR'] * 0.4, self.customData['calleeR'] * 0.4)
		return r

	def getBodyRadius(self):
		r = 8
		if self.kind != ITEM_VARIABLE:
			r = math.pow(float(self.lines+1), 0.3) * 5.0
		return r

	def getHeight(self):
		h = (self.fontSize.height() + self.commentSize.height())*1.67
		return h

	def getLeftSlotPos(self):
		l = self.getBodyRadius()
		if self.isFunction():
			l += self.customData['callerR']
		return self.pos() + QtCore.QPointF(-l, 0)

	def getRightSlotPos(self):
		l = self.getBodyRadius()
		if self.isFunction():
			l += self.customData['calleeR']
		return self.pos() + QtCore.QPointF(l, 0)

	def boundingRect(self):
		r = self.getBodyRadius()
		adj = r * 2 # 10
		if self.isFunction():
			adj = max(self.customData['callerR'], self.customData['calleeR'], adj)
		return QtCore.QRectF(-r-adj, -r-adj, r*2 + adj*2, r*2 + adj*2)

	def shape(self):
		r = self.getBodyRadius()
		path = QtGui.QPainterPath()
		path.addEllipse(-r,-r,r*2,r*2)
		return path

	def getCallerRadius(self, num):
		return math.log2(float(num+1.0)) * 5.0

	def paint(self, painter, styleOptionGraphicsItem, widget_widget=None):
		#super(CodeUIItem, self).paint(painter, styleOptionGraphicsItem, widget_widget)

		painter.setRenderHint(QtGui.QPainter.Antialiasing)
		painter.setRenderHint(QtGui.QPainter.TextAntialiasing)
		r = self.getBodyRadius()
 
		trans = painter.worldTransform()
		lod = QtGui.QStyleOptionGraphicsItem().levelOfDetailFromTransform(trans)

		selectedOrHover = self.isSelected() or self.isHover

		if r * lod > 1.0:
			# if self.selectCounter > 0:
			# 	gradR = r * 2
			# 	gradient = QtGui.QRadialGradient(0,0,gradR,0,0);
			# 	gradient.setColorAt(1.0/3.0, QtGui.QColor(255,233,155,100))
			# 	gradient.setColorAt(1,       QtGui.QColor(255,233,155,0))
			# 	#painter.setBrush(QtGui.QBrush(gradient))
			# 	bright = min(255, math.log2(float(self.selectCounter+1.0)) * 20.0)
			# 	print('bright', bright, self.selectCounter)
			# 	painter.setBrush(QtGui.QBrush(QtGui.QColor(255,233,155,bright)))
			# 	painter.setPen(QtCore.Qt.NoPen)
			# 	painter.drawEllipse(QtCore.QPointF(0,0),gradR,gradR)

			if selectedOrHover:
				pen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(255,157,38,255)), 20.0)#, QtCore.Qt.SolidLine, QtCore.Qt.SquareCap, QtCore.Qt.RoundJoin)
				painter.setPen(pen)
				self.drawShape(painter)

			painter.setPen(QtCore.Qt.NoPen)

			clr = self.color
			if self.isFunction():
				#clr = clr.lighter(130)
				painter.setBrush(clr)
				nCaller = self.customData.get('nCaller', 0)
				nCallee = self.customData.get('nCallee', 0)
				# print('ncall', nCaller, nCallee)
				if nCaller > 0:
					cr = self.customData['callerR']
					painter.drawPie(-r-cr, -cr, cr*2, cr*2, 160*16, 40*16)
				if nCallee > 0:
					cr = self.customData['calleeR']
					painter.drawPie(r-cr, -cr, cr*2, cr*2, -20*16, 40*16)

			clr = self.color
			# if selectedOrHover:
			# 	clr = clr.darker(130)
			painter.setBrush(clr)
			self.drawShape(painter)

			if self.lines == 0 and self.kind == ITEM_FUNCTION:
				painter.setBrush(QtGui.QColor(50,50,50,255))
				painter.setPen(QtCore.Qt.NoPen)
				painter.drawEllipse(QtCore.QPointF(0,0),2.5,2.5)

		if r * lod > 3 or selectedOrHover:
			painter.scale(1.0/lod, 1.0/lod)
			painter.setPen(QtGui.QPen()) 
			painter.setFont(self.titleFont)
			if self.kind == ITEM_VARIABLE:
				rect = QtCore.QRectF(r, self.lineHeight*-0.5, self.fontSize.width(), self.fontSize.height())
			else:
				rect = QtCore.QRectF(0, 0, self.fontSize.width(), self.fontSize.height())

			dx = 1.0
			painter.setPen(QtGui.QPen(QtGui.QColor(50,50,50)))
			rect0 = rect.translated(dx,dx)
			painter.drawText(rect0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, self.displayName)

			painter.setPen(QtGui.QPen(QtGui.QColor(255,239,183)))
			painter.drawText(rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, self.displayName)

			scene = self.scene()
			commentData = scene.itemDataDict.get(self.uniqueName, {}).get('comment')
			if commentData:
				painter.setPen(QtGui.QPen(QtGui.QColor(166,241,27)))
				rect.moveTop(rect.bottom())
				rect.setSize(QtCore.QSizeF(100,500))
				painter.drawText(rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop | QtCore.Qt.TextWordWrap, commentData)



	def drawShape(self, painter):
		r = self.getBodyRadius()
		if self.kind == ITEM_FUNCTION:
			painter.drawEllipse(-r,-r,r*2,r*2)
		elif self.kind == ITEM_VARIABLE:
			painter.drawPolygon(QtCore.QPoint(-r,0), QtCore.QPoint(r,-r), QtCore.QPoint(r,r))
		elif self.kind == ITEM_CLASS:
			painter.drawRect(-r,-r,r*2,r*2)

	def contextMenuEvent(self, event):
		#print ('context menu')

		from UIManager import UIManager
		#UIManager.instance().getScene().clearSelection()
		#self.setSelected(True)

		itemMenu = UIManager.instance().getMainUI().getItemMenu()
		itemMenu.exec(event.screenPos())

	def mousePressEvent(self, event):
		super(CodeUIItem, self).mousePressEvent(event)
		self.displayScore += 1
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.autoFocus = False

		# if event.button() == QtCore.Qt.MidButton:
		# 	self.setCursor(QtCore.Qt.ClosedHandCursor)

	def mouseReleaseEvent(self, event):
		super(CodeUIItem, self).mouseReleaseEvent(event)
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.autoFocus = True

		# if event.button() == QtCore.Qt.MidButton:
		# 	self.setCursor(QtCore.Qt.OpenHandCursor)


	def mouseDoubleClickEvent(self, event):
		super(CodeUIItem, self).mouseDoubleClickEvent(event)

		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.showInEditor()


	def mouseMoveEvent(self, event):
		super(CodeUIItem, self).mouseMoveEvent(event)
		if self.isSelected():
			self.targetPos = QtCore.QPointF(self.pos().x(), self.pos().y())

		if event.buttons().__int__() & QtCore.Qt.MidButton or event.buttons().__int__() & QtCore.Qt.RightButton:
			print('event button:', event.buttons().__int__())
			drag = QtGui.QDrag(event.widget())
			mime = QtCore.QMimeData()
			mime.setText(self.uniqueName)
			drag.setMimeData(mime)
			drag.exec()
			#self.setCursor(QtCore.Qt.OpenHandCursor)

	def hoverLeaveEvent(self, QGraphicsSceneHoverEvent):
		super(CodeUIItem, self).hoverLeaveEvent(QGraphicsSceneHoverEvent)
		self.isHover = False

	def hoverEnterEvent(self, QGraphicsSceneHoverEvent):
		super(CodeUIItem, self).hoverEnterEvent(QGraphicsSceneHoverEvent)
		self.isHover = True

	def dragEnterEvent(self, event):
		#print('drag', event, event.source())
		event.setAccepted(True)

	def dropEvent(self, event):
		super(CodeUIItem, self).dropEvent(event)
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if not scene:
			return

		mouseButtons = event.buttons()
		if mouseButtons & QtCore.Qt.MiddleButton:
			srcName = event.mimeData().text()
			srcItem = scene.getNode(srcName)
			if not srcItem:
				return
			#print('src is function', srcItem.isFunction() , self.isFunction())
			if not srcItem.isFunction() or not self.isFunction():
				return
			scene.addCallPaths(srcName, self.uniqueName)
		elif mouseButtons & QtCore.Qt.RightButton:
			srcName = event.mimeData().text()
			srcItem = scene.getNode(srcName)
			if not srcItem:
				return
			scene.addCustomEdge(srcName, self.uniqueName, {})

if __name__ == "__main__":
	import re
	p = re.compile(r'([A-Z]*[a-z0-9]*_*)')
	s = 'aa_bbAbbbAAbbb_aa_123__'
	print(p.findall(s))