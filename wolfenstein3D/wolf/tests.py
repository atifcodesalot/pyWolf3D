import unittest

from .gamemaps import *
from .wolfenstein import *


class ParserTest(unittest.TestCase):
    def test_parse(self):
        maphead = open(path.join("assets", "maps", "MAPHEAD.WL1"), "rb")
        maptemp = open(path.join("assets", "maps", "MAPTEMP.WL1"), "rb")
        parser = GameMapsParser(maphead.read(), maptemp.read(), level_count=10)
        maphead.close()
        maptemp.close()
        self.assertEqual(parser.magic_marker, 0xABCD)
        self.assertEqual(len(parser.level_offsets), 10)
        self.assertEqual(len(parser.planes), 10)

    def test_decompress(self):
        maphead = open(path.join("assets", "maps", "MAPHEAD.WL1"), "rb")
        maptemp = open(path.join("assets", "maps", "MAPTEMP.WL1"), "rb")
        parser = GameMapsParser(maphead.read(), maptemp.read(), level_count=10)
        maphead.close()
        maptemp.close()
        plane = [0xA, 0x00, 0xCD, 0xAB, 0x03, 0x00,
                 0x01, 0x00, 0x02, 0x00, 0x03, 0x00]
        decompressed = parser.decompress(plane)
        self.assertEqual(
            decompressed, [0x0001, 0x0001, 0x0001, 0x0002, 0x0003])

    def test_shareware_maps(self):
        self.assertEqual(len(SHAREWARE_MAPS), 10)
        for wolfmap in SHAREWARE_MAPS:
            self.assertIsInstance(wolfmap, WolfMap)


class WolfGameTest(unittest.TestCase):
    def test_actor_instances(self):
        mymap = SHAREWARE_MAPS[4]
        self.assertFalse(id(mymap.actors[0]) == id(mymap.actors[1]))
        self.assertFalse(id(mymap.actors[0].sprites[0]) == id(
            mymap.actors[1].sprites[0]))

    def test_blocking_sprites(self):
        for _map in SHAREWARE_MAPS:
            self.assertTrue(
                any([sprite.blocking for sprite in _map.sprites])
            )
            
    def test_actor_sprite_count(self):
        for _map in SHAREWARE_MAPS:
            for actor in _map.actors:
                self.assertGreater(len(actor.sprites), 8*4)
                self.assertEqual(len(actor.sprites[0].image.getdata()), 64*64)

    def test_quick_render(self):
        mymap = SHAREWARE_MAPS[0]
        mymap.add_item(WolfItem.CHAINGUN, (400, 400))
        player = WolfPlayer(mymap, ray_count=128, weapon=WolfWeapon.MP4)
        player.ammo = 5
        screen = pygame.display.set_mode((128*4, 128*4))
        sw, sh = screen.get_size()
        renderer = WolfRenderer(player, screen)
        game = WolfGame(player, renderer)
        raycaster = game.renderer.raycaster
        self.assertEqual(raycaster.observer.pos, player.pos)
        map_ = raycaster.map
        self.assertEqual(map_.size, (64, 64))
        bird_view = pygame.Surface(
            (map_.wall_width * map_.size[0], map_.wall_width * map_.size[1]))
        bw_scale = 0.25
        while game.ongoing:
            game.heartbeat()
            screen.blit(pygame.transform.scale(
                bird_view, (int(sw * bw_scale), int(sh * bw_scale))), (0, 0))
            bird_view.fill((0, 0, 0))
            raycaster.render_bird_view(renderer.colls, pygame, bird_view)
            pygame.display.flip()

    # def test_character_sprites(self):
    #     self.assertIn("guard", SPRITES["characters"])
    #     guard_sprites = SPRITES["characters"]["guard"]
    #     self.assertIsInstance(guard_sprites, dict)
    #     self.assertGreater(len(guard_sprites), 0)
    #     guard_sprites[1].image.show()


if __name__ == '__main__':
    unittest.main()
