# -*- coding: utf-8 -*-
from PyQt4 import QtCore, Qt
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
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
	KIND_UNKNOWN = 0
	KIND_MEMBER  = 1
	KIND_CALL    = 2
	KIND_DERIVE  = 3
	KIND_USE	 = 4
	KIND_OVERRIDE= 5

	# Dict for (kind, isReverse)
	kindDict = {
		'reference'		: (KIND_UNKNOWN,	False),
		'unknown'		: (KIND_UNKNOWN,	False),
		'call'			: (KIND_CALL, 		False),
		'callby'		: (KIND_CALL, 		True),
		'base'			: (KIND_DERIVE, 	True),
		'derive'		: (KIND_DERIVE, 	False),
		'use'			: (KIND_USE, 		False),
		'useby'			: (KIND_USE, 		True),
		'member'		: (KIND_MEMBER, 	False),
		'declare'		: (KIND_MEMBER, 	False),
		'define'		: (KIND_MEMBER, 	False),
		'declarein'		: (KIND_MEMBER, 	True),
		'definein' 		: (KIND_MEMBER, 	True),
		'override'		: (KIND_OVERRIDE,	True),
		'overrides'		: (KIND_OVERRIDE,	True),
		'overriddenby'	: (KIND_OVERRIDE,	False),
	}
	def __init__(self, srcId, dstId, refKindStr):
		self.srcId = srcId
		self.dstId = dstId
		self.kind = IndexRefItem.kindDict.get(refKindStr, (IndexRefItem.KIND_UNKNOWN, False))[0]

class XmlDocItem(object):
	CACHE_NONE = 0
	CACHE_REF  = 1
	def __init__(self, doc):
		self.doc = doc
		self.cacheStatus = 0

	def getDoc(self):
		return self.doc

	def getCacheStatus(self, status):
		return (self.cacheStatus & status) > 0

	def setCacheStatus(self, status):
		self.cacheStatus = self.cacheStatus | status

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
	def __init__(self, kind, entity):
		self.kind = kind
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
		self.xmlCache = {}			# xml file name -> XmlDocItem
		self.xmlElementCache = {}	# dict for xml element, id -> xmlElement

	def _getXmlDocument(self, fileName):
		return self._getXmlDocumentItem(fileName).getDoc()

	def _getXmlDocumentItem(self, fileName):
		filePath = '%s/%s.xml' % (self._dbFolder, fileName)
		xmlDoc = self.xmlCache.get(filePath)
		if xmlDoc:
			return xmlDoc
		doc = ET.parse(filePath)
		xmlDoc = XmlDocItem(doc)
		self.xmlCache[filePath] = xmlDoc
		return xmlDoc

	def _readIndex(self):
		if not self._dbFolder:
			return
		doc = self._getXmlDocument('index')

		compoundList = doc.findall("compound")
		for compound in compoundList:
			compoundRefId = compound.attrib.get('refid','')

			# record name attr
			for compoundChild in compound.getchildren():
				if compoundChild.tag == 'name':
					self.idInfoDict[compoundRefId] = \
						IndexItem(compoundChild.text, compound.attrib.get('kind'), compoundRefId)
					break

			# list members
			memberList = compound.findall("member")
			refIdList = []
			for member in memberList:
				# build member -> compound dict
				memberRefId = member.attrib.get('refid')
				self.idToCompoundDict[memberRefId] = compoundRefId
				refIdList.append(memberRefId)

				#recode name attr
				for memberChild in member.getchildren():
					if memberChild.tag == 'name':
						self.idInfoDict[memberRefId] = \
							IndexItem(memberChild.text, member.attrib.get('kind'), memberRefId)
						break

			# build compound -> member dict
			self.compoundToIdDict[compoundRefId] = refIdList

	def _readRef(self, compoundId):
		doc = self._getXmlDocument(compoundId)
		if not doc:
			return

		xmlDocItem = self._getXmlDocumentItem(compoundId)
		if xmlDocItem.getCacheStatus(XmlDocItem.CACHE_REF):
			return

		# build references
		compoundDefList = doc.findall("compounddef")
		for compoundDef in compoundDefList:
			compoundId = compoundDef.attrib.get('id')
			compoundItem = self.idInfoDict.get(compoundId)
			if not compoundItem:
				continue

			for compoundChild in compoundDef.getchildren():
				# find base classes
				if compoundChild.tag == 'basecompoundref':
					baseCompoundId = compoundChild.attrib.get('refid')
					baseCompoundItem = self.idInfoDict.get(baseCompoundId)
					if baseCompoundItem:
						refItem = IndexRefItem(baseCompoundId, compoundId, 'derive')
						baseCompoundItem.addRefItem(refItem)
						compoundItem.addRefItem(refItem)

				# find derived classes
				if compoundChild.tag == 'derivedcompoundref':
					derivedCompoundId = compoundChild.attrib.get('refid')
					derivedCompoundItem = self.idInfoDict.get(derivedCompoundId)
					if derivedCompoundItem:
						refItem = IndexRefItem(compoundId, derivedCompoundId, 'derive')
						derivedCompoundItem.addRefItem(refItem)
						compoundItem.addRefItem(refItem)

				# find members
				if compoundChild.tag == 'listofallmembers':
					memberList = compoundChild.findall('member')
					for member in memberList:
						memberId = member.attrib.get('refid')
						memberItem = self.idInfoDict.get(memberId)
						if memberItem and compoundItem:
							refItem = IndexRefItem(compoundId, memberId, 'member')
							memberItem.addRefItem(refItem)
							compoundItem.addRefItem(refItem)

				# find members' refs
				if compoundChild.tag == 'sectiondef':
					for sectionChild in compoundChild.getchildren():
						if sectionChild.tag == 'memberdef':
							memberDef = sectionChild
							memberId = memberDef.attrib.get('id')
							memberItem = self.idInfoDict.get(memberId)

							for memberChild in memberDef.getchildren():
								if memberChild.tag == 'references':
									referenceId = memberChild.attrib.get('refid')
									referenceItem = self.idInfoDict.get(referenceId)
									if memberItem and referenceItem:
										refItem = IndexRefItem(memberId, referenceId, 'unknown')
										memberItem.addRefItem(refItem)
										referenceItem.addRefItem(refItem)

								if memberChild.tag == 'referencedby':
									referenceId = memberChild.attrib.get('refid')
									referenceItem = self.idInfoDict.get(referenceId)
									if memberItem and referenceItem:
										refItem = IndexRefItem(referenceId, memberId, 'unknown')
										memberItem.addRefItem(refItem)
										referenceItem.addRefItem(refItem)

								# find override methods
								if memberChild.tag == 'reimplementedby':
									overrideId = memberChild.attrib.get('refid')
									overrideItem = self.idInfoDict.get(overrideId)
									if overrideItem:
										refItem = IndexRefItem(memberId, overrideId, 'overrides')
										overrideItem.addRefItem(refItem)
										memberItem.addRefItem(refItem)

								if memberChild.tag == 'reimplements':
									interfaceId = memberChild.attrib.get('refid')
									interfaceItem = self.idInfoDict.get(interfaceId)
									if interfaceItem:
										refItem = IndexRefItem(interfaceId, memberId, 'overrides')
										interfaceItem.addRefItem(refItem)
										memberItem.addRefItem(refItem)
		xmlDocItem.setCacheStatus(XmlDocItem.CACHE_REF)

	def _readRefs(self):
		if not self._dbFolder:
			return
		for compoundId, _ in self.compoundToIdDict.items():
			self._readRef(compoundId)

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
			memberList = doc.findall('./compounddef/sectiondef/memberdef')
			for member in memberList:
				if member.attrib.get('id') == refid:
					self.xmlElementCache[refid] = member
					return member
		elif refid in self.compoundToIdDict:
			doc = self._getXmlDocument(refid)
			compoundList = doc.findall('compounddef')
			for compound in compoundList:
				if compound.attrib.get('id') == refid:
					self.xmlElementCache[refid] = compound
					return compound
		return None

	def _parseLocationDict(self, element):
		line = int(element.attrib.get('line'))
		column = int(element.attrib.get('column'))

		file = element.attrib.get('bodyfile')
		if not file:
			file = element.attrib.get('file')

		bodyStart = element.attrib.get('bodystart')
		bodyEnd = element.attrib.get('bodyend')

		start = int(bodyStart) if bodyStart else -1
		end   = int(bodyEnd)   if bodyEnd   else -1
		return {'file': file, 'line': line, 'column': column, 'CountLine': max(end - start+1, 0)}

	def _parseEntity(self, element):
		if not element:
			return None
		if element.tag == 'compounddef':
			name = ''
			longName = ''
			kind = element.attrib.get('kind')
			metric = None
			id = element.attrib.get('id')
			for elementChild in element.getchildren():
				if elementChild.tag == 'compoundname':
					name = elementChild.text
					longName = name
				elif elementChild.tag == 'location':
					metric = self._parseLocationDict(elementChild)
			return Entity(id, name, longName, kind, metric)
		elif element.tag == 'memberdef':
			name = ''
			longName = ''
			kind = element.attrib.get('kind')
			virt = element.attrib.get('virt')
			if virt == 'virtual':
				kind = 'virtual ' + kind
			elif virt == 'pure-virtual':
				kind = 'pure virtual ' + kind
			metric = None
			id = element.attrib.get('id')
			for elementChild in element.getchildren():
				if elementChild.tag == 'name':
					name = elementChild.text
				elif elementChild.tag == 'definition':
					longName = elementChild.text
				elif elementChild.tag == 'location':
					metric = self._parseLocationDict(elementChild)
			return Entity(id, name, longName, kind, metric)
		else:
			return None

	def open(self, fullPath):
		if self._dbFolder:
			self.close()
		self._dbFolder = os.path.split(fullPath)[0]
		self._readIndex()
		# self._readRefs()

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
			if kind != None and info.kind != kind:
				continue
			if nameLower in info.name.lower():
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
		refKindList = []
		if refKindStr:
			refKindStr = refKindStr.lower()
			pattern = re.compile('[a-z]+')
			refNameList =pattern.findall(refKindStr)
			for refName in refNameList:
				refKindList.append(IndexRefItem.kindDict.get(refName, (IndexRefItem.KIND_UNKNOWN, False)))

		# parse entKindStr
		entKindList = []
		if entKindStr:
			entKindNameStr = entKindStr.lower()
			pattern = re.compile('[a-z]+')
			entKindNameList = pattern.findall(entKindNameStr)
			for entKindName in entKindNameList:
				entKindList.append(IndexItem.kindDict.get(entKindName, 0))

		# build reference link
		compoundId = self.idToCompoundDict.get(uniqueName)
		if not compoundId:
			compoundId = uniqueName
		self._readRef(compoundId)

		# find references
		refEntityList = []
		refRefList    = []
		refs = thisItem.getRefItemList()
		for ref in refs:
			otherId = ref.srcId
			if ref.srcId == uniqueName:
				otherId = ref.dstId
			otherItem = self.idInfoDict.get(otherId)
			if not otherItem:
				continue
			if len(entKindList) > 0 and otherItem.kind not in entKindList:
				continue
			otherEntity = self.searchFromUniqueName(otherId)
			if not otherEntity:
				continue

			# match each ref kind
			for refKind, isExchange in refKindList:
				srcItem = thisItem
				dstItem = otherItem
				if isExchange:
					srcItem = otherItem
					dstItem = thisItem\

				# check edge direction
				if srcItem.id != ref.srcId or dstItem.id != ref.dstId:
					continue

				isAccepted = False
				if refKind == IndexRefItem.KIND_CALL and ref.kind == IndexRefItem.KIND_UNKNOWN:
					if  srcItem.kind == IndexItem.KIND_FUNCTION and dstItem.kind == IndexItem.KIND_FUNCTION:
						isAccepted = True
				elif refKind == IndexRefItem.KIND_MEMBER and ref.kind == IndexRefItem.KIND_MEMBER:
					if  srcItem.kind in (IndexItem.KIND_CLASS, IndexItem.KIND_STRUCT) and\
						dstItem.kind in (IndexItem.KIND_CLASS, IndexItem.KIND_STRUCT, IndexItem.KIND_FUNCTION, IndexItem.KIND_VARIABLE, IndexItem.KIND_SIGNAL, IndexItem.KIND_SLOT):
						isAccepted = True
				elif refKind == IndexRefItem.KIND_USE and ref.kind == IndexRefItem.KIND_UNKNOWN:
					if  srcItem.kind in (IndexItem.KIND_FUNCTION,) and\
						dstItem.kind in (IndexItem.KIND_VARIABLE,):
						isAccepted = True
				elif refKind == IndexRefItem.KIND_DERIVE and ref.kind == IndexRefItem.KIND_DERIVE:
					if  srcItem.kind in (IndexItem.KIND_CLASS, IndexItem.KIND_STRUCT) and\
						dstItem.kind in (IndexItem.KIND_CLASS, IndexItem.KIND_STRUCT):
						isAccepted = True
				elif refKind == IndexRefItem.KIND_OVERRIDE and ref.kind == IndexRefItem.KIND_OVERRIDE:
					isAccepted = True

				if isAccepted:
					refEntityList.append(otherEntity)
					refRefList.append(Reference(refKind, otherEntity))

		return refEntityList, refRefList

	def searchRefEntity(self, uniqueName, refKindStr = None, entKindStr = None, isUnique = True):
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
	# db.open('I:/Programs/masteringOpenCV/Chapter3_MarkerlessAR/doc/xml/index.xml')
	db.open('I:/Programs/mitsuba/doxygenData/xml/index.xml')
	# element = db._getXmlElement('main_8cpp_1aff21477595f55398a44d72df24d4d6c5')
	#classA = db.search('ARDrawingContext', 'class')[0]
	#functionA = db.search('drawCoordinateAxis', 'function')[0]
	#varA = db.search('m_windowName', 'variable')[0]

	refList, entList = db._searchRef(classA.uniquename(), 'member', 'variable', True)
	# db.open('D:/Code/NewRapidRT/rapidrt/doxygen/xml/index.xml')
	# element = db._getXmlElement('classcpplint_1_1___block_info_1a02a0b48995a599f6b2bbaa6f16cca98a')
	# db.search('AGeometry', 'class')
	# db.search('getOrCreateAccelStruct', 'function')
	# db.search('m_pUserData', 'variable')

