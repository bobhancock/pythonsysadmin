import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../dry'))
import date

class TestDate(unittest.TestCase):
	def testNonIntMonth(self):
		self.assertRaises(ValueError, date.intMonthToString, 'a')
	
	def testIntMonthTooSmall(self):
		self.assertRaises(ValueError, date.intMonthToString, 0)
	
	def testIntMonthTooBig(self):
		self.assertRaises(ValueError, date.intMonthToString, 13)

	def testexttime(self):
		fname = 'testme.txt'
		f = date.exttime(fname)
		self.assertNotEqual(fname, f)
		
def suite():
	dateTestSuite = unittest.makeSuite(TestDate, 'test')
	return suite
	
if __name__ == "__main__":
	unittest.main()

