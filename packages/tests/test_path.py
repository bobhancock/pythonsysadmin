import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../dry'))
import path

class TestPath(unittest.TestCase):
	def setUp(self):
		self.badDir = '/usr'
		self.listBadDirs = ['aksdjf', 'sakdjf', '/dkjf/ere/tt']
		self.listGoodDirs = ['/usr', '/tmp', '/var/tmp']
		self.listGoodFiles = ['/etc/passwd', '/etc/group']
		self.listBadFiles = ['akdjf', '/I/do/not/exist']
	
	
	def test_isDirWriteable(self):
		res = path.isDirWriteable(self.badDir)
		self.assertEqual(False, res)
		
	def test__bad_arenotDirs(self):
		res = path.arenotDirs(self.listBadDirs)
		self.assertEqual(len(self.listBadDirs), len(res))
		
	def test_good_arenotDirs(self):
		res = path.arenotDirs(self.listGoodDirs)
		self.assertEqual(res, None)
		
	def test_good_arenotFiles(self):
		res = path.arenotFiles(self.listBadFiles)
		self.assertEqual(len(self.listBadFiles), len(res))
		
	def test_bad_arentoFiles(self):
		res = path.arenotFiles(self.listGoodFiles);
		self.assertEqual(None, res)
		
if __name__ == "__main__":
	unittest.main()

