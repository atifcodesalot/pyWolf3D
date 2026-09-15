
from .raycaster import *
from .aux_math import *
from .renderer import RayRenderer, PointLight
from .textures import *
import cProfile
import pygame
from .sprites import *


profiler = cProfile.Profile()


def observer_test():
    o = Observer((150, 150))
    try:
        assert len(o.directions) == o.ray_count
    except AssertionError:
        print("Ray count mismatch")
        print(f"Expected {o.ray_count}, got {len(o.directions)}")


def map_test():
    map = WolfMap((30, 30), wall_width=10)
    assert map.raw

    try:
        assert not map.in_boundary((301, 301))
    except AssertionError:
        print("Map in_boundary test failed")

    map.raw[28][26] = 1

    try:
        assert map.get_cell((26*10, 28*10))
    except AssertionError:
        print("Map get_cell test failed")


def raycaster_test():
    o = Observer((100, 100), look_dir=[-1, 0], ray_count=80)
    map_ = WolfMap((30, 30), wall_width=16)
    map_.set_random(50)
    screen = pygame.display.set_mode(
        (map_.wall_width * map_.size[0], map_.wall_width * map_.size[1]))
    raycaster = Raycaster(o, map_)
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
        screen.fill((0, 0, 0))

        colls, _ = raycaster.raycast()
        o.rotate(1)

        raycaster.render_bird_view(colls, pygame, screen)
        pygame.display.flip()
        clock.tick(60)


def renderer_test():
    o = Observer((100, 100), look_dir=[-1, 0], ray_count=200, fov=60)
    map_ = WolfMap((30, 30), wall_width=16)
    map_.set_random(10, 3)
    map_.set_random(10, 2)
    screen = pygame.display.set_mode((600, 600))
    sw, sh = screen.get_size()
    raycaster = Raycaster(o, map_)
    renderer = RayRenderer(raycaster, screen)
    renderer.add_sprite(SPRITES["characters/fake_hitler.png"], pos=(25, 25))
    renderer.add_sprite(SPRITES["object29"], pos=(30, 25))
    renderer.add_sprite(SPRITES["object30"], pos=(35, 30))
    renderer.add_sprite(SPRITES["object31"], pos=(30, 35))
    renderer.add_sprite(SPRITES["object35"], pos=(50, 55))
    renderer.add_sprite(SPRITES["object32"], pos=(65, 55))
    renderer.add_sprite(SPRITES["object32"], pos=(100, 55))
    renderer.add_sprite(SPRITES["object34"], pos=(200, 55))

    bird_view = pygame.Surface(
        (map_.wall_width * map_.size[0], map_.wall_width * map_.size[1]))
    bw_scale = 0.25
    clock = pygame.time.Clock()
    light = PointLight(o.pos)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_LEFT]:
            o.rotate(-2)
        if pressed[pygame.K_RIGHT]:
            o.rotate(2)
        if pressed[pygame.K_UP]:
            o.translate((o.look_dir[0]*2, o.look_dir[1]*2))
        if pressed[pygame.K_DOWN]:
            o.translate((-o.look_dir[0]*2, -o.look_dir[1]*2))
        light.pos = o.pos
        screen.fill((0, 0, 0))
        renderer.cast()
        renderer.render(light)
        screen.blit(pygame.transform.scale(
            bird_view, (int(sw * bw_scale), int(sh * bw_scale))), (0, 0))
        bird_view.fill((0, 0, 0))
        raycaster.render_bird_view(renderer.colls, pygame, bird_view)
        pygame.display.flip()
        clock.tick(60)


def texture_tests():
    import time
    screen = pygame.display.set_mode((128, 128))
    tex = WALL_TEXTURES[0]
    for i, c in enumerate(tex.columns):
        screen.blit(tex.get_column(i, 1, 128-i, 1, 128), (i, 0))
        pygame.display.flip()
        time.sleep(0.001)


def sprite_tests():
    import random
    o = Observer((300, 300), look_dir=[-1, 0], ray_count=300, fov=60)
    map_ = WolfMap((30, 30), wall_width=16)
    screen = pygame.display.set_mode((600, 600))
    sw, sh = screen.get_size()
    raycaster = Raycaster(o, map_)
    renderer = RayRenderer(raycaster, screen)
    for sprite in list(SPRITES.values())[:5]:
        randangle = math.radians(random.choice(range(0, 360, 30)))
        renderer.add_sprite(sprite, (25 * math.cos(randangle) + 300,
                                     25 * math.sin(randangle) + 300))
    bird_view = pygame.Surface(
        (map_.wall_width * map_.size[0], map_.wall_width * map_.size[1]))
    bw_scale = 0.25
    clock = pygame.time.Clock()
    light = PointLight(o.pos)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
        light.pos = o.pos
        screen.fill((0, 0, 0))
        renderer.cast()
        renderer.render(light)
        screen.blit(pygame.transform.scale(
            bird_view, (int(sw * bw_scale), int(sh * bw_scale))), (0, 0))
        bird_view.fill((0, 0, 0))
        raycaster.render_bird_view(renderer.colls, pygame, bird_view)
        pygame.display.flip()
        clock.tick(60)
        o.rotate(1)


def main():
    texture_tests()
    observer_test()
    map_test()
    raycaster_test()
    profiler.enable()
    renderer_test()
    profiler.disable()
    profiler.dump_stats("raycaster.prof")
    sprite_tests()


if __name__ == "__main__":
    main()
