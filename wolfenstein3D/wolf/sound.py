
from raycaster.aux_math import *
from . import pygame
from .assets import SOUNDS
from math import pow
from dataclasses import dataclass


# get 32 channels
pygame.mixer.set_num_channels(32)


@dataclass
class WolfSoundEffect:
    snd: pygame.mixer.Sound
    origin: tuple
    volume: float
    channel: pygame.mixer.Channel


class WolfSoundManager:
    def __init__(self, master, music_vol=0.8):
        self.master = master
        self.music_vol = self.cap_volume(music_vol)
        self.sndeff_queue = {}
        self.playing_effects = []
        self.heartbeats = 0
        self.channel_count = pygame.mixer.get_num_channels()

    def cap_volume(self, vol):
        # cap to master
        return min(vol, self.master)

    @staticmethod
    def attenuate_func(x):
        x = 1 if x == 0 else x
        return 15/pow(x, 2)

    def attenuate(self, origin, game_ctx):
        if origin is None:
            return self.master
        pblock = game_ctx.player.get_current_block()
        oblock = game_ctx.wolfmap.to_block_pos(*origin)
        dist = euclidean_distance(pblock, oblock)
        level = self.cap_volume(self.attenuate_func(dist))
        return level

    def queue_sound_effect(self, snd: pygame.mixer.Sound, origin, game_ctx, _time):
        sndeff = WolfSoundEffect(snd, origin, None, None)
        sndeff.volume = self.attenuate(origin, game_ctx)
        future = game_ctx.heartbeats +_time
        while future in self.sndeff_queue:
            future += 1
        self.sndeff_queue[future] = sndeff

    def handle_queue(self, game_ctx):
        now = game_ctx.heartbeats 
        if now not in self.sndeff_queue:
            return
        sndeff = self.sndeff_queue.pop(now)
        self.start_sound_effect(sndeff)

    def handle_sound(self, game_ctx):
        self.handle_queue(game_ctx)
        for sndeff in self.playing_effects:
            if sndeff.channel.get_busy():
                # if the sound is still playing
                dynamic = self.attenuate(sndeff.origin, game_ctx)
                sndeff.channel.set_volume(dynamic)
            else:
                self.playing_effects.remove(sndeff)

    def start_sound_effect(self, sndeff):
        ch = sndeff.snd.play()
        if ch is None:
            ch = pygame.mixer.find_channel(force=True)
        sndeff.channel = ch
        # cap to master before playing
        sndeff.channel.set_volume(self.master)
        # add to the playing sounds
        self.playing_effects.append(sndeff)

    def play_music(self, piece):
        pygame.mixer.music.load(SOUNDS["music"][piece])
        pygame.mixer.music.set_volume(self.music_vol)
        pygame.mixer.music.play(loops=-1)

    def set_master(self, new):
        if new > 1:
            new = 1
        elif new < 0:
            new = 0
        self.master = new
        self.set_music_volume(self.master)

    def set_music_volume(self, new):
        self.music_vol = self.cap_volume(new)
