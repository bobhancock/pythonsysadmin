import unittest
import socket
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../dry'))
import mail

class TestMail(unittest.TestCase):
	def setUp(self):
		self.mailserver = 'gdpmail1.mhf2.mhf.mhc'
		self.goodEmail = 'thomas.edison@ge.com'
		self.badEmail = 'thomas.edison&ge.com'
		self.goodMailServers = [self.mailserver, 'gdpmail2.mhf2.mhf.mhc']
		self.badMailServers = ['badvalue', 'worsevalue', 'worstvalue']
		
	def test_NotAServer(self):
		self.assertRaises(socket.gaierror, mail.isMaillServerAvailable, 'notaserver')
		
	def test_EhloTrue(self):
		res = mail.isMaillServerAvailable(self.mailserver)
		self.assertEqual(res, True)
		
	def test_firstMaillServerAvailable(self):
		firstSever = mail.firstMaillServerAvailable(self.goodMailServers)
		self.assertEqual(self.mailserver, firstSever)
	
	def test_NoMaillServerAvailable(self):
		self.assertRaises(socket.gaierror, mail.firstMaillServerAvailable, self.badMailServers)
		
	def test_ValidEmail(self):
		res = mail.isValidEmail(self.goodEmail)
		self.assertEqual(True, res)
		
	def test_InvalidEmail(self):
		res = mail.isValidEmail(self.badEmail)
		self.assertEqual(False, res)
		
	def test_NoMailServersSpecified(self):
		res = mail.firstMaillServerAvailable([])
		self.assertEqual(res, None)
		
	def test_InvalidMailServers(self):
		lm = ['junk', 'morejunk']
		self.assertRaises(Exception asmail.setupMailServer, lm)
		
	def test_ValidInvalidMailServers(self):
		lm = ['junk', 'gdpmail1.mhf2.mhf.mhc']
		self.assertRaises(Exception asmail.setupMailServer, lm)
		
def suite():
	dateTestSuite = unittest.makeSuite(TestMail, 'test')
	return suite
	
if __name__ == "__main__":
	unittest.main()

