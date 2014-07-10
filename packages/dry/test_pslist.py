import unittest
import system

class TestPSList(unittest.TestCase):
    def setUp(self):
        self.pslist = system.PSList()
        self.entry = 'rhancock  2240  2072  0 Apr23 ?   00:00:00 python  /usr/share/system-config-printer/applet.py\n'
        self.pslist.inmem_pslist += self.entry

    def tearDown(self):
        pass

    def test_uid(self):
        res = self.pslist.find(uid='rhancock')
        self.assertNotEqual(0, len(res))
        
    def test_not_uid(self):
        res = self.pslist.find(uid='rhancockX')
        self.assertEqual(0, len(res))
    
    #def test_pid(self):
        #res = self.pslist.find(pid='2240')
        #self.assertNotEqual(0, len(res))
        
    #def test_not_pid(self):
        #res = self.pslist.find(pid='22409')
        #self.assertEqual(0, len(res))
        
    #def test_ppid(self):
        #res = self.pslist.find(ppid='2072')
        #self.assertNotEqual(0, len(res))
        
    #def test_not_ppid(self):
        #res = self.pslist.find(ppid='22409')
        #self.assertEqual(0, len(res))
            
    #def test_c(self):
        #res = self.pslist.find(c='0')
        #self.assertNotEqual(0, len(res))
        
    #def test_not_c(self):
        #res = self.pslist.find(c='22409')
        #self.assertEqual(0, len(res))
        
    #def test_stime(self):
        #res = self.pslist.find(stime='Apr23')
        #self.assertNotEqual(0, len(res))
        
    #def test_not_stime(self):
        #res = self.pslist.find(stime='22409')
        #self.assertEqual(0, len(res))
            
    #def test_tty(self):
        #res = self.pslist.find(tty='?')
        #self.assertNotEqual(0, len(res))
        
    #def test_not_tty(self):
        #res = self.pslist.find(tty='22409')
        #self.assertEqual(0, len(res))

    #def test_time(self):
        #res = self.pslist.find(time='00:00:00')
        #self.assertNotEqual(0, len(res))
        
    #def test_not_time(self):
        #res = self.pslist.find(time='22409')
        #self.assertEqual(0, len(res))
        
    #def test_cmd(self):
        #res = self.pslist.find(cmd='system-config-printer')
        #self.assertNotEqual(0, len(res))
        
    #def test_not_cmd(self):
        #res = self.pslist.find(cmd='22409')
        #self.assertEqual(0, len(res))        

    #def test_cmd_exact(self):
        #res = self.pslist.find(cmd='system-config-printer', cmd_exact_match=False)
        #self.assertNotEqual(0, len(res))
        
    #def test_not_cmd_exact(self):
        #res = self.pslist.find(cmd='system-config-printer', cmd_exact_match=True)
        #self.assertEqual(0, len(res))        
        
if __name__ == "__main__":
    unittest.main()

