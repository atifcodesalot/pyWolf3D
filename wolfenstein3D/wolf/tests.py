
import unittest
from .gamemaps import *
from .wolfenstein import *
from .game_objects import *
import cProfile


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
        mymap = SHAREWARE_MAPS[1]
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

    def test_quick(self):
        mymap = SHAREWARE_MAPS[0]
        player = WolfPlayer(mymap, ray_count=160,
                            weapon=WolfWeapon.PISTOL, fov=54)
        player.ammo = 10
        screen = pygame.display.set_mode((680, 600))
        game = WolfGame(player, root_display=screen, sound_off=False, noclip=False)
        raycaster = game.game_renderer.raycaster
        self.assertEqual(raycaster.observer.pos, player.pos)
        map_ = raycaster.map
        self.assertEqual(map_.size, (64, 64))
        game.mainloop()

    def test_weapon_sprites(self):
        self.assertIn("weapons", SPRITES)
        weapons = SPRITES["weapons"]
        self.assertIsInstance(weapons, dict)
        self.assertGreater(len(weapons), 0)
        # weapons[1].image.show()

    def test_object_sprites(self):
        self.assertIn("objects", SPRITES)
        objects = SPRITES["objects"]
        self.assertIsInstance(objects, dict)
        self.assertGreater(len(objects), 0)
        # objects[1].image.show()
        
    def test_actor_positions_middle(self):
        for _map in SHAREWARE_MAPS:
            for actor in _map.actors:
                self.assertEqual(actor.pos[0] % _map.wall_width, _map.wall_width // 2)
                self.assertEqual(actor.pos[1] % _map.wall_width, _map.wall_width // 2)

    # def test_maps(self):
    #     for wolfmap in SHAREWARE_MAPS:
    #         self.assertIsInstance(wolfmap, WolfMap)
    #         self.assertGreater(len(wolfmap.actors), 0)
    #         self.assertGreater(len(wolfmap.sprites), 0)

    # def test_character_sprites(self):
    #     self.assertIn("guard", SPRITES["characters"])
    #     guard_sprites = SPRITES["characters"]["guard"]
    #     self.assertIsInstance(guard_sprites, dict)
    #     self.assertGreater(len(guard_sprites), 0)
    #     guard_sprites[1].image.show()


if __name__ == '__main__':
    # uncomment to profile
    # with cProfile.Profile() as pr:
        unittest.main(exit=False)

    # pr.dump_stats("wolf.prof")
