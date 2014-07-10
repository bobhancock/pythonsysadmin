import unittest
import rx_rsync
import multiprocessing
import collections

class test_find_files_to_compress(unittest.TestCase):
    """ Check types passed and if directory for os.walk exists. """
    def setUp(self):
        product_conf = collections.namedtuple("product_conf", "local_root")
        self.pc = product_conf("/xxx")
        self.q = multiprocessing.JoinableQueue()
        
    def test_product_conf_list(self):
        self.assertRaises(TypeError, rx_rsync.find_files_to_compress, {}, self.q)
        
    def test_output_q(self):
        self.assertRaises(TypeError, rx_rsync.find_files_to_compress, self.pc, "")
        
    def test_local_root(self):
        self.assertRaises(IOError, rx_rsync.find_files_to_compress, self.pc, self.q)
        
if __name__ == "__main__":
    unittest.main()