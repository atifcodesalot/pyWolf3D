
import pygame
import logging

pygame.font.init()
pygame.mixer.init()

SPRITES = {}
WALL_TEXTURES = {}

wolflogger = logging.getLogger(__package__)
wolflogger.setLevel(logging.INFO)
logging.basicConfig(level=logging.DEBUG,
                    format="[%(asctime)s]==[%(name)s]==[%(levelname)s]: %(message)s")