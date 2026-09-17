import unittest

from .gamemaps_parser import *
from .wolf import *


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
        plane = [0xA, 0x00, 0xCD, 0xAB, 0x03, 0x00,
                 0x01, 0x00, 0x02, 0x00, 0x03, 0x00]
        decompressed = parser.decompress(plane)
        self.assertEqual(
            decompressed, [0x0001, 0x0001, 0x0001, 0x0002, 0x0003])
        maphead.close()
        maptemp.close()

    def test_shareware_maps(self):
        self.assertEqual(len(SHAREWARE_MAPS), 10)
        for wolfmap in SHAREWARE_MAPS:
            self.assertIsInstance(wolfmap, WolfMap)


class WolfGameTest(unittest.TestCase):
    def test_quick(self):
        player = WolfPlayer((10, 10), SHAREWARE_MAPS[0])
        screen = pygame.display.set_mode((128*4, 128*4))
        sw, sh = screen.get_size()
        renderer = WolfRenderer(player, screen)
        game = WolfGame(player, renderer, [])
        raycaster = game.renderer.raycaster
        self.assertEqual(raycaster.observer.pos, player.pos)
        map_ = raycaster.map
        self.assertEqual(map_.size, (64, 64))
        bird_view = pygame.Surface(
            (map_.wall_width * map_.size[0], map_.wall_width * map_.size[1]))
        bw_scale = 0.25
        while True:
            game.heartbeat()
            screen.blit(pygame.transform.scale(
                                    bird_view, (int(sw * bw_scale), int(sh * bw_scale))), (0, 0))
            
            raycaster.render_bird_view(renderer.colls, pygame, bird_view)
            pygame.display.flip()


if __name__ == '__main__':
    unittest.main()
