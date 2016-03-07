# -*- coding: utf-8 -*-
import sys
#print sys.path
#sys.path.append('D:/Program Files (x86)/SciTools/bin/pc-win32/python')
import understand
import subprocess

class CodeDB(object):
	def __init__(self):
		self._db = None
		self._dbPath = ''

	def open(self, path):
		if self._db:
			self._db.close()
		self._dbPath = path
		self._db = understand.open(path)
		print('open', self._db)

	def close(self):
		if self._db:
			self._db.close()

	def analyze(self):
		if self._db and self._dbPath:
			self._db.close()

			cmdStr = r'und analyze "%s"' % self._dbPath
			print(cmdStr)
			workingPath = r'D:\Program Files (x86)\SciTools\bin\pc-win32'
			p = subprocess.Popen(cmdStr, cwd = workingPath)
			p.wait()

			self._db = understand.open(self._dbPath)

	def search(self, name, kindstring = None):
		if not self._db:
			return []
		res = self._db.lookup(name, kindstring)
		return res

	def searchFromUniqueName(self, uniqueName):
		if not self._db:
			return None
		return self._db.lookup_uniquename(uniqueName)

	def searchRefEntity(self, uniqueName, refKindStr, entKindStr, isUnique = True):
		ent = self._db.lookup_uniquename(uniqueName)
		if not ent:
			return []

		refList = ent.refs(refKindStr, entKindStr, isUnique)
		entList = [refObj.ent().uniquename() for refObj in refList]
		#print('entList', entList)
		return entList

	def searchRef(self, uniqueName, refKindStr, entKindStr, isUnique = True):
		ent = self._db.lookup_uniquename(uniqueName)
		if not ent:
			return []

		refList = ent.refs(refKindStr, entKindStr, isUnique)
		return refList