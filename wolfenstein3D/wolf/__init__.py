
import pygame
import logging

pygame.font.init()
pygame.mixer.init(44100, -16, 2, 512) 
pygame.init()

SPRITES = {}
WALL_TEXTURES = {}

wolflogger = logging.getLogger(__package__)
wolflogger.setLevel(logging.INFO)
logging.basicConfig(level=logging.DEBUG,
                    format="[%(asctime)s]==[%(name)s]==[%(levelname)s]: %(message)s")