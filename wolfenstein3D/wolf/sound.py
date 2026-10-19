
from wolfenstein3D.raycaster.aux_math import *
from wolfenstein3D.wolf import pygame
from wolfenstein3D.wolf.assets import SOUNDS
from math import pow, pi, atan2
from dataclasses import dataclass


# increase this value as you wish
CHANNEL_AMOUNT = 32

# get 32 channels
pygame.mixer.set_num_channels(CHANNEL_AMOUNT)


@dataclass
class WolfSoundEffect:
    snd: pygame.mixer.Sound
    origin: tuple
    volume: float
    channel: pygame.mixer.Channel
    repeat: bool


class WolfSoundManager:
    direction_conf = [
        (0.707, 0.707),
        (0.5, 0.86),
        (0, 1),
        (0.5, 0.86),
        (0.707, 0.707),
        (0.86, 0.5),
        (1, 0),
        (0.86, 0.5)
    ]

    def __init__(self, master, music_vol=0.1):
        self.master = master
        self.music_vol = self.cap_volume(music_vol)
        self.sndeff_queue = {}
        self.playing_effects = []
        self.heartbeats = 0
        self.channel_count = pygame.mixer.get_num_channels()
        pygame.mixer.set_reserved(1)
        self.norepeat_channel = pygame.mixer.Channel(0)

    def cap_volume(self, vol):
        # cap to master
        return min(vol, self.master)

    def sound_sector(self, origin, game_ctx, sectors=8):
        sx, sy = game_ctx.player.to_this_space(origin)
        return int((pi/2-atan2(-sy, sx)) // (2*pi / sectors) % sectors)

    def pan(self, sndeff: WolfSoundEffect, game_ctx):
        if sndeff.origin is None:
            return
        sector = self.sound_sector(sndeff.origin, game_ctx)
        dir_conf = self.direction_conf[sector]
        sndeff.channel.set_volume(*vec_mul(dir_conf, sndeff.volume))

    @staticmethod
    def attenuate_func(x):
        x = 1 if x == 0 else x
        return 10/pow(x, 2)

    def attenuate(self, sndeff, game_ctx):
        if sndeff.origin is None:
            return self.master
        pblock = game_ctx.player.get_current_block()
        oblock = game_ctx.wolfmap.to_block_pos(*sndeff.origin)
        dist = euclidean_distance(pblock, oblock)
        level = self.cap_volume(self.attenuate_func(dist))
        sndeff.volume = level
        sndeff.channel.set_volume(sndeff.volume)

    def already_in_queue(self, snd: pygame.mixer.Sound):
        return snd in self.sndeff_queue

    def already_playing(self, snd: pygame.mixer.Sound):
        return snd.get_num_channels() > 0

    def queue_sound_effect(self, snd: pygame.mixer.Sound,
                           origin, game_ctx, _time, repeat=True):

        sndeff = WolfSoundEffect(snd, origin, None, None, repeat=repeat)
        future = game_ctx.heartbeats + _time
        while future in self.sndeff_queue:
            future += 1
        self.sndeff_queue[future] = sndeff

    def handle_queue(self, game_ctx):
        now = game_ctx.heartbeats
        if now not in self.sndeff_queue:
            return
        sndeff = self.sndeff_queue.pop(now)
        self.start_sndeff(sndeff)

    def handle_sound(self, game_ctx):
        self.handle_queue(game_ctx)
        for sndeff in self.playing_effects:
            if sndeff.origin is None:
                continue
            if sndeff.channel.get_busy():
                # if the sound is still playing
                self.adjust_sndeff(sndeff, game_ctx)
            else:
                # if not remove it
                self.playing_effects.remove(sndeff)

    def adjust_sndeff(self, sndeff: WolfSoundEffect, game_ctx):
        self.attenuate(sndeff, game_ctx=game_ctx)
        self.pan(sndeff, game_ctx=game_ctx)

    def start_sndeff(self, sndeff: WolfSoundEffect):
        if not sndeff.repeat:
            if self.norepeat_channel.get_busy():
                self.norepeat_channel.stop()
            self.norepeat_channel.play(sndeff.snd)
            sndeff.channel = self.norepeat_channel
            self.norepeat_channel.play(sndeff.snd)
        else:
            ch = sndeff.snd.play()
            if ch is None:
                ch = pygame.mixer.find_channel(force=True)
            sndeff.channel = ch
        # cap to master before playing
        sndeff.channel.set_volume(self.master)
        # add to the playing sounds
        self.playing_effects.append(sndeff)

    # music related methods start here
    def play_music(self, piece):
        pygame.mixer.music.load(SOUNDS["music"][piece])
        pygame.mixer.music.set_volume(self.music_vol)
        pygame.mixer.music.play(loops=-1)

    def stop_music(self):
        pygame.mixer.music.stop()

    def pause_music(self):
        pygame.mixer.music.pause()

    def continue_music(self):
        pygame.mixer.music.unpause()

    def set_music_volume(self, new):
        self.music_vol = self.cap_volume(new)
    ###
    ###

    def set_master(self, new):
        if new > 1:
            new = 1
        elif new < 0:
            new = 0
        self.master = new
        self.set_music_volume(self.master)
