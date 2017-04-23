# -*- coding: utf-8 -*-
from PyQt4 import QtCore, Qt
from xml.dom import minidom
import re
import os

# Used internally by DoxygenDB
class IndexItem(object):
	KIND_UNKNOWN = 0
	# compound
	KIND_CLASS = 1
	KIND_STRUCT = 2
	KIND_UNION = 3
	KIND_INTERFACE = 4
	KIND_PROTOCOL = 5
	KIND_CATEGORY = 6
	KIND_EXCEPTION = 7
	KIND_FILE = 8
	KIND_NAMESPACE = 9
	KIND_GROUP = 10
	KIND_PAGE = 11
	KIND_EXAMPLE = 12
	# member
	KIND_DIR = 13
	KIND_DEFINE = 14
	KIND_PROPERTY = 15
	KIND_EVENT = 16
	KIND_VARIABLE = 17
	KIND_TYPEDEF = 18
	KIND_ENUM = 19
	KIND_ENUMVALUE = 20
	KIND_FUNCTION = 21
	KIND_SIGNAL = 22
	KIND_PROTOTYPE = 23
	KIND_FRIEND = 24
	KIND_DCOP = 25
	KIND_SLOT = 26

	kindDict = {
		'unknown':KIND_UNKNOWN,			'class':KIND_CLASS,				'struct':KIND_STRUCT,
		'union':KIND_UNION,				'interface':KIND_INTERFACE,		'protocol':KIND_PROTOCOL,
		'category':KIND_CATEGORY,		'exception':KIND_EXCEPTION,		'file':KIND_FILE,
		'namespace':KIND_NAMESPACE,		'group':KIND_GROUP,				'page':KIND_PAGE,
		'example':KIND_EXAMPLE,			'dir':KIND_DIR,					'define':KIND_DEFINE,
		'property':KIND_PROPERTY,		'event':KIND_EVENT,				'variable':KIND_VARIABLE,
		'typedef':KIND_TYPEDEF,			'enum':KIND_ENUM,				'enumvalue':KIND_ENUMVALUE,
		'function':KIND_FUNCTION,		'signal':KIND_SIGNAL,			'prototype':KIND_PROTOTYPE,
		'friend':KIND_FRIEND,			'dcop':KIND_DCOP,				'slot':KIND_SLOT,
		# extra keywords
		'method':KIND_FUNCTION
		}

	def __init__(self, name, kindStr, id):
		self.id   = id
		self.name = name
		self.kind = IndexItem.kindDict.get(kindStr, 0)
		self.refs = []

	def isCompoundKind(self):
		return 1 <= self.kind <= 13

	def isMemberKind(self):
		return 14 <= self.kind <= 26

	def addRefItem(self, ref):
		self.refs.append(ref)

	def getRefItemList(self):
		return self.refs

class IndexRefItem(object):
	kindDict = {
		'unknown': 0,
		'member' : 1,
		}

	def __init__(self, srcItem, dstItem, refKindStr):
		self.srcItem = srcItem
		self.dstItem = dstItem
		self.kind = IndexRefItem.kindDict.get(refKindStr, 0)

# Used by public APIs of DoxygenDB
class Entity(object):
	def __init__(self, id, name, longName, kindName, metric):
		self.id = id
		self.shortName = name
		self.longName = longName
		self.kindName = kindName
		self.metricDict = metric

	def name(self):
		return self.shortName

	def longname(self):
		return self.longName

	def uniquename(self):
		return self.id

	def kindname(self):
		return self.kindName

	def metric(self, keys = None):
		if not keys:
			return self.metricDict
		return {k: self.metricDict.get(k) for k in keys}

class Reference(object):
	def __init__(self, kindString, entity):
		self.kind = kindString
		self.entityId = entity.id
		self.entity = entity
		self.entityLocationDict = entity.metric()

	def file(self):
		fileName = self.entityLocationDict.get('file','')
		return Entity('', fileName, fileName, 'file', {})

	def line(self):
		return self.entityLocationDict.get('line', -1)

	def column(self):
		return self.entityLocationDict.get('column', -1)

	def ent(self):
		return None

class DoxygenDB(QtCore.QObject):
	reopenSignal = QtCore.pyqtSignal()
	def __init__(self):
		super(DoxygenDB, self).__init__()
		self._dbFolder = ''
		self.reopenSignal.connect(self.reopen, Qt.Qt.QueuedConnection)
		self.idToCompoundDict = {}	# dict for   member objects, member   id -> compound id
		self.compoundToIdDict = {}	# dict for compound objects, compound id -> [refid, refid, ...]
		self.idInfoDict = {}		# info for both compound and member object, id -> IndexItem
		self.xmlCache = {}			# xml file name -> xml document
		self.xmlElementCache = {}	# dict for xml element, id -> xmlElement

	def _getXmlDocument(self, fileName):
		filePath = '%s/%s.xml' % (self._dbFolder, fileName)
		xmlDoc = self.xmlCache.get(filePath)
		if xmlDoc:
			return xmlDoc
		xmlDoc = minidom.parse(filePath)
		self.xmlCache[filePath] = xmlDoc
		return xmlDoc

	def _readIndex(self):
		if not self._dbFolder:
			return
		doc = self._getXmlDocument('index')

		compoundList = doc.getElementsByTagName("compound")
		for compound in compoundList:
			compoundRefId = compound.getAttribute('refid')

			# record name attr
			for compoundChild in compound.childNodes:
				if compoundChild.nodeName == 'name':
					self.idInfoDict[compoundRefId] = \
						IndexItem(compoundChild.childNodes[0].data, compound.getAttribute('kind'), compoundRefId)
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
							IndexItem(memberChild.childNodes[0].data, member.getAttribute('kind'), memberRefId)
						break

			# build compound -> member dict
			self.compoundToIdDict[compoundRefId] = refIdList

	def _readRefs(self):
		if not self._dbFolder:
			return
		for compoundId, _ in self.compoundToIdDict.items():
			doc = self._getXmlDocument(compoundId)
			if not doc:
				continue
			compoundDefList = doc.getElementsByTagName("compounddef")
			for compoundDef in compoundDefList:
				compoundId = compoundDef.getAttribute('id')
				compoundItem = self.idInfoDict.get(compoundId)

				# find members
				listOfAllMembersList = compoundDef.getElementsByTagName('listofallmembers')
				for listOfAllMembers in listOfAllMembersList:
					memberList = listOfAllMembers.getElementsByTagName('member')
					for member in memberList:
						memberId = member.getAttribute('refid')
						memberItem = self.idInfoDict.get(memberId)
						if memberItem and compoundItem:
							refItem = IndexRefItem(compoundItem, memberItem, 'member')
							memberItem.addRefItem(refItem)
							compoundItem.addRefItem(refItem)

				# find members' refs
				sectionDefList = compoundDef.getElementsByTagName('sectiondef')
				for sectionDef in sectionDefList:
					memberDefList = sectionDef.getElementsByTagName('memberdef')
					for memberDef in memberDefList:
						memberId = memberDef.getAttribute('id')
						memberItem = self.idInfoDict.get(memberId)

						referenceList = memberDef.getElementsByTagName('references')
						for reference in referenceList:
							referenceId = reference.getAttribute('refid')
							referenceItem = self.idInfoDict.get(referenceId)
							if memberItem and referenceItem:
								refItem = IndexRefItem(memberItem, referenceItem, 'reference')
								memberItem.addRefItem(refItem)
								referenceItem.addRefItem(refItem)

						referencedbyList = memberDef.getElementsByTagName('referencedby')
						for reference in referencedbyList:
							referenceId = reference.getAttribute('refid')
							referenceItem = self.idInfoDict.get(referenceId)
							if memberItem and referenceItem:
								refItem = IndexRefItem(referenceItem, memberItem, 'reference')
								memberItem.addRefItem(refItem)
								referenceItem.addRefItem(refItem)

	def _isCompound(self, refid):
		return refid in self.compoundToIdDict.keys()

	def _isMember(self, refid):
		return refid in self.idToCompoundDict.keys()

	def _getXmlElement(self, refid):
		if not self._dbFolder:
			return None
		element = self.xmlElementCache.get(refid)
		if element:
			return element

		if refid in self.idToCompoundDict:
			fileName = self.idToCompoundDict.get(refid)
			doc = self._getXmlDocument(fileName)
			memberList = doc.getElementsByTagName('memberdef')
			for member in memberList:
				if member.getAttribute('id') == refid:
					self.xmlElementCache[refid] = member
					return member
		elif refid in self.compoundToIdDict:
			doc = self._getXmlDocument(refid)
			compoundList = doc.getElementsByTagName('compounddef')
			for compound in compoundList:
				if compound.getAttribute('id') == refid:
					self.xmlElementCache[refid] = compound
					return compound
		return None

	def _parseLocationDict(self, element):
		file = element.getAttribute('bodyfile')
		line = int(element.getAttribute('line'))
		column = int(element.getAttribute('column'))
		start = int(element.getAttribute('bodystart'))
		end = int(element.getAttribute('bodyend'))
		return {'file': file, 'line': line, 'column': column, 'CountLine': end - start+1}

	def _parseEntity(self, element):
		if not element:
			return None
		if element.nodeName == 'compounddef':
			name = ''
			longName = ''
			kind = element.getAttribute('kind')
			metric = None
			id = element.getAttribute('id')
			for elementChild in element.childNodes:
				if elementChild.nodeName == 'compoundname':
					name = elementChild.childNodes[0].data
					longName = name
				elif elementChild.nodeName == 'location':
					metric = self._parseLocationDict(elementChild)
			return Entity(id, name, longName, kind, metric)
		elif element.tagName == 'memberdef':
			name = ''
			longName = ''
			kind = element.getAttribute('kind')
			metric = None
			id = element.getAttribute('id')
			for elementChild in element.childNodes:
				if elementChild.nodeName == 'name':
					name = elementChild.childNodes[0].data
				elif elementChild.nodeName == 'definition':
					longName = elementChild.childNodes[0].data
				elif elementChild.nodeName == 'location':
					metric = self._parseLocationDict(elementChild)
			return Entity(id, name, longName, kind, metric)
		else:
			return None

	def open(self, fullPath):
		self._dbFolder = os.path.split(fullPath)[0]
		self._readIndex()
		self._readRefs()

	def getDBPath(self):
		return self._dbFolder + '/index.xml'

	def close(self):
		self._dbFolder = ''
		self.idToCompoundDict = {}
		self.compoundToIdDict = {}
		self.idInfoDict = {}
		self.xmlCache = {}
		self.xmlElementCache = {}

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
		nameLower = name.lower()
		for id, info in self.idInfoDict.items():
			if nameLower in info.name.lower():
				if kind != None and info.kind != kind:
					continue

				xmlElement = self._getXmlElement(id)
				if not xmlElement:
					continue
				entity = self._parseEntity(xmlElement)
				#entity = Entity(id, info.name, info.kind)
				res.append(entity)
		return res

	def searchFromUniqueName(self, uniqueName):
		if not self._dbFolder:
			return None
		xmlElement = self._getXmlElement(uniqueName)
		if not xmlElement:
			return None
		entity = self._parseEntity(xmlElement)
		return entity

	def _searchRef(self, uniqueName, refKindStr = None, entKindStr = None, isUnique = True):
		thisItem = self.idInfoDict.get(uniqueName)
		if not thisItem:
			return [], []

		# parse refKindStr
		refNameList = []
		if refKindStr:
			refKindStr = refKindStr.lower()
			pattern = re.compile('[a-z]+')
			refNameList =pattern.findall(refKindStr)

		# parse entKindStr
		entKindList = []
		if entKindStr:
			entKindNameStr = entKindStr.lower()
			pattern = re.compile('[a-z]+')
			entKindNameList = pattern.findall(entKindNameStr)
			for entKindName in entKindNameList:
				entKindList.append(IndexItem.kindDict.get(entKindName, 0))

		refEntityList = []
		refRefList    = []
		thisEntity = self.searchFromUniqueName(uniqueName)
		refs = thisItem.getRefItemList()

		for ref in refs:
			otherItem = self.idInfoDict.get(ref.dstItem.id if ref.srcItem == thisItem else uniqueName)
			if not otherItem:
				continue
			if len(entKindList) > 0 and otherItem.kind not in entKindList:
				continue
			otherEntity = self.searchFromUniqueName(otherItem.id)
			if not otherEntity:
				continue

			# match each ref kind
			for refName in refNameList:
				isAccepted = False

				refKindName = refName
				srcItem = thisItem
				dstItem = otherItem
				# exchange src and dst when get 'callby' 'useby' ...
				if refKindName.endswith('by'):
					refKindName = refKindName[0:-2]
					srcItem = otherItem
					dstItem = thisItem

				if refKindName == 'call':
					if  srcItem.kind == IndexItem.KIND_FUNCTION and dstItem.kind == IndexItem.KIND_FUNCTION:
						isAccepted = True
				elif refKindName == 'member':
					if  srcItem.kind  in (IndexItem.KIND_CLASS, IndexItem.KIND_STRUCT) and\
						dstItem.kind in (IndexItem.KIND_CLASS, IndexItem.KIND_STRUCT, IndexItem.KIND_FUNCTION, IndexItem.KIND_VARIABLE, IndexItem.KIND_SIGNAL, IndexItem.KIND_SLOT):
						isAccepted = True
				elif refKindName == 'use':
					if  srcItem.kind in (IndexItem.KIND_FUNCTION,) and\
						dstItem.kind in (IndexItem.KIND_VARIABLE,):
						isAccepted = True

				if isAccepted:
					refEntityList.append(otherEntity)
					refRefList.append(Reference(refName, otherEntity))

		return refEntityList, refRefList

	def searchRefEntity(self, uniqueName, refKindStr, entKindStr, isUnique = True):
		refEntityList, refRefList = self._searchRef(uniqueName, refKindStr, entKindStr, isUnique)
		return refEntityList, refRefList

	def searchRefObj(self, srcUName, tarUName):
		refEntityList, refRefList = self._searchRef(srcUName)
		for i in range(len(refEntityList)):
			if refEntityList[i].uniquename() == tarUName:
				return refRefList[i]
		return None

	def searchRef(self, uniqueName, refKindStr = None, entKindStr = None, isUnique = True):
		refEntityList, refRefList = self._searchRef(uniqueName, refKindStr, entKindStr, isUnique)
		return refRefList
	
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
	db.open('I:/Programs/masteringOpenCV/Chapter3_MarkerlessAR/doc/xml/index.xml')
	# element = db._getXmlElement('main_8cpp_1aff21477595f55398a44d72df24d4d6c5')
	classA = db.search('ARDrawingContext', 'class')[0]
	functionA = db.search('drawCoordinateAxis', 'function')[0]
	varA = db.search('m_windowName', 'variable')[0]

	refList, entList = db._searchRef(classA.uniquename(), 'member', 'variable', True)
	# db.open('D:/Code/NewRapidRT/rapidrt/doxygen/xml/index.xml')
	# element = db._getXmlElement('classcpplint_1_1___block_info_1a02a0b48995a599f6b2bbaa6f16cca98a')
	# db.search('AGeometry', 'class')
	# db.search('getOrCreateAccelStruct', 'function')
	# db.search('m_pUserData', 'variable')

