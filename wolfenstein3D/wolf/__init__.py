
import pygame
import logging

pygame.font.init()

SPRITES = {}
WALL_TEXTURES = {}

wolflogger = logging.getLogger(__package__)
logging.basicConfig(level=logging.DEBUG,
                    format="[%(asctime)s]==[%(name)s]==[%(levelname)s]: %(message)s")