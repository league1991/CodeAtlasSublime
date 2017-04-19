# -*- coding: utf-8 -*-
from PyQt4 import QtCore, Qt
from xml.dom import minidom

# Used internally by DoxygenDB
class IndexItem(object):
	kindDict = {
		'unknown':0,

		'class':1,
		'struct':2,
		'union':3,
		'interface':4,
		'protocol':5,
		'category':6,
		'exception':7,
		'file':8,
		'namespace':9,
		'group':10,
		'page':11,
		'example':12,
		'dir':13,

		'define':14,
		'property':15,
		'event':16,
		'variable':17,
		'typedef':18,
		'enum':19,
		'enumvalue':20,
		'function':21,
		'signal':22,
		'prototype':23,
		'friend':24,
		'dcop':25,
		'slot':26 }

	def __init__(self, name, kindStr):
		self.name = name
		self.kind = IndexItem.kindDict.get(kindStr)
		if not self.kind:
			self.kind = 0

	def isCompoundKind(self):
		return 1 <= self.kind <= 13

	def isMemberKind(self):
		return 14 <= self.kind <= 26

# Used by public APIs of DoxygenDB
class Entity(object):
	def __init__(self, id, name, kind):
		self.id = id
		self.name = name
		self.kind = kind

	def name(self):
		return ''

	def longname(self):
		return ''

	def uniquename(self):
		return ''

	def kindname(self):
		return ''

	def refs(self):
		return ''

	def metric(self):
		return {'CountLine':0}

class Reference(object):
	def __init__(self):
		pass

	def file(self):
		pass

	def line(self):
		pass

	def column(self):
		pass

class DoxygenDB(QtCore.QObject):
	reopenSignal = QtCore.pyqtSignal()
	def __init__(self):
		super(DoxygenDB, self).__init__()
		self._dbFolder = ''
		self.reopenSignal.connect(self.reopen, Qt.Qt.QueuedConnection)
		self.idToCompoundDict = {}	# refid -> compound id
		self.compoundToIdDict = {}	# coompound id -> [refid, refid, ...]
		self.idInfoDict = {}		# id -> IndexItem

	def _readIndex(self):
		if not self._dbFolder:
			return
		doc = minidom.parse(self._dbFolder + '/index.xml')

		compoundList = doc.getElementsByTagName("compound")
		for compound in compoundList:
			compoundRefId = compound.getAttribute('refid')

			# record name attr
			for compoundChild in compound.childNodes:
				if compoundChild.nodeName == 'name':
					self.idInfoDict[compoundRefId] = \
						IndexItem(compoundChild.childNodes[0].data, compound.getAttribute('kind'))
					break

			# list members
			memberList = compound.getElementsByTagName("member")
			refIdList = []
			for member in memberList:
				# build member -> compound dict
				memberRefId = member.getAttribute('refid')
				self.idToCompoundDict[memberRefId] = compoundRefId
				refIdList.append(memberRefId)

				#recode name attr
				for memberChild in member.childNodes:
					if memberChild.nodeName == 'name':
						self.idInfoDict[memberRefId] = \
							IndexItem(memberChild.childNodes[0].data, member.getAttribute('kind'))
						break

			# build compound -> member dict
			self.compoundToIdDict[compoundRefId] = refIdList

	def _isCompound(self, refid):
		return refid in self.compoundToIdDict.keys()

	def _isMember(self, refid):
		return refid in self.idToCompoundDict.keys()

	def _getXmlElement(self, refid):
		if not self._dbFolder:
			return None

		if refid in self.idToCompoundDict:
			fileName = self.idToCompoundDict.get(refid)
			doc = minidom.parse('%s/%s.xml' % (self._dbFolder, fileName))
			memberList = doc.getElementsByTagName('memberdef')
			for member in memberList:
				if member.getAttribute('id') == refid:
					return member
		elif refid in self.compoundToIdDict:
			doc = minidom.parse('%s/%s.xml' % (self._dbFolder, refid))
			compoundList = doc.getElementsByTagName('compounddef')
			for compound in compoundList:
				if compound.getAttribute('id') == refid:
					return compound

		return None

	def _parseXmlElement(self, element):
		if not element:
			return None
		if element.nodeName == 'compounddef':
			for elementChild in element.childNodes:
				if elementChild.nodeName == 'compoundname':
					pass
		elif element.tagName == 'memberdef':
			pass

	def open(self, path):
		self._dbFolder = path
		self._readIndex()

	def getDBPath(self):
		return self._dbFolder + '/index.xml'

	def close(self):
		pass

	@QtCore.pyqtSlot()
	def reopen(self):
		pass

	def analyze(self):
		pass

	def onOpen(self):
		pass

	def search(self, name, kindstring = None):
		if not name:
			return []

		res = []
		kind = IndexItem.kindDict.get(kindstring.lower())
		for id, info in self.idInfoDict.items():
			if name in info.name:
				if kind != None and info.kind != kind:
					continue

				xmlElement = self._getXmlElement(id)
				if not xmlElement:
					continue
				entity = self._parseXmlElement(xmlElement)
				#entity = Entity(id, info.name, info.kind)
				res.append(entity)
		return res

	def searchFromUniqueName(self, uniqueName):
		pass

	def searchRefEntity(self, uniqueName, refKindStr, entKindStr, isUnique = True):
		return [],[]

	def searchRefObj(self, srcUName, tarUName):
		return None

	def searchRef(self, uniqueName, refKindStr, entKindStr, isUnique = True):
		return []
	
	def searchCallPaths(self, srcUniqueName, tarUniqueName):
		return [],[]

	def listFiles(self):
		return

	def buildSymbolTree(self):
		return None, None

	def _buildSymbolTreeRecursive(self, symbol):
		return


def printSymbolDict(sym, indent = 0):
	for uname, childSym in sym.childrenDict.items():
		printSymbolDict(childSym, indent+1)

if __name__ == "__main__":
	db = DoxygenDB()
	db.open('I:/Programs/masteringOpenCV/Chapter3_MarkerlessAR/doc/xml/')
	element = db._getXmlElement('main_8cpp_1aff21477595f55398a44d72df24d4d6c5')

	db.search('ARDrawingContext', 'class')
	db.search('drawCoordinateAxis', 'function')
	db.search('m_windowName', 'variable')
	#db.open('C:/Users/me/AppData/Roaming/Sublime Text 3/Packages/CodeAtlas/codeatlassublime.udb')
	#db.listFiles()
	#root = db.buildSymbolTree()

	#printSymbolDict(root)
	#db.close()

