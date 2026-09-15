import unittest

from .gamemaps_parser import *

class ParserTest(unittest.TestCase):
    def test_parse(self):
        maphead = open(path.join("maps", "MAPHEAD.WL1"), "rb")
        maptemp = open(path.join("maps", "MAPTEMP.WL1"), "rb")
        parser = Parser(maphead.read(), maptemp.read(), level_count=10)
        self.assertEqual(parser.magic_marker, 0xABCD)
        self.assertEqual(len(parser.level_offsets), 10)
        self.assertEqual(len(parser.planes), 10)
        maphead.close()
        maptemp.close()
        
    def test_decompress(self):
        maphead = open(path.join("maps", "MAPHEAD.WL1"), "rb")
        maptemp = open(path.join("maps", "MAPTEMP.WL1"), "rb")
        parser = Parser(maphead.read(), maptemp.read(), level_count=10)
        plane = [0xA, 0x00, 0xCD, 0xAB, 0x03, 0x00, 0x01, 0x00, 0x02, 0x00, 0x03, 0x00]
        decompressed = parser.decompress(plane)
        self.assertEqual(decompressed, [0x0001, 0x0001, 0x0001, 0x0002, 0x0003])
        maphead.close()
        maptemp.close()
    
    def test_shareware_maps(self):
        self.assertEqual(len(SHAREWARE_MAPS), 10)
        for wolfmap in SHAREWARE_MAPS:
            self.assertIsInstance(wolfmap, WolfMap)

        

if __name__ == '__main__':
    unittest.main()