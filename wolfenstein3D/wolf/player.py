

from wolfenstein3D.raycaster.raycaster import Observer
from wolfenstein3D.wolf.game_objects import WolfWeapon
from wolfenstein3D.wolf.maps import WolfMap
from wolfenstein3D.raycaster.aux_math import *
from wolfenstein3D.wolf.actors import Actor
import pygame


from math import acos, degrees


class WolfPlayer(Observer):
    def __init__(self, game, fov=60,
                 ray_count=256, health=100, weapon=WolfWeapon.PISTOL, ammo=10):
        self.game = game
        map_ = self.game.wolfmap
        super().__init__(
            map_.init_pos.copy(), map_, map_.init_look.copy(), fov, ray_count)
        self.weapon = weapon
        self.pace = 0.7
        self.rot_pace = 2.0

        self.health = health
        self.ammo = ammo
        self.score = 0
        self.lives = 5

        self.has_gold_key = False
        self.has_silver_key = False

        self.shooting = False
        self.running = False

        self.acquired_weapons = set(
            [WolfWeapon.PISTOL, WolfWeapon.KNIFE, self.weapon])

        # for now
        self.excited_to_kill_nazis = False

    def has_auto(self):
        return self.weapon.value > 1

    def look_at(self, point):
        self.look_dir = vec_norm(vec_sub(self.pos, point))
        self.left = vec_get_perp(self.look_dir)
        self.update_directions()

    def update_look_dir(self, newldir):
        self.look_dir = vec_norm(newldir)
        self.left = vec_get_perp(self.look_dir)
        self.update_directions()

    def turn_cc(self, mag=1):
        self.rotate(mag*self.rot_pace)

    def turn_cw(self, mag=1):
        self.rotate(-mag*self.rot_pace)

    def out_of_ammo(self):
        return self.ammo == 0

    def get_current_block(self):
        return self.map.to_block_pos(*self.pos)
    
    def get_current_cell(self):
        pblock = self.map.to_block_pos(*self.pos)
        return self.map.raw[pblock[1]][pblock[0]]

    def get_current_area(self):
        pblock = self.get_current_block()
        cell = self.map.raw[pblock[1]][pblock[0]]
        if self.map.cell_is_door(cell):
            # if inside door tile, return the second area
            return self.map.get_door(pblock).area1
        return cell - 107

    def get_front_cell(self):
        pblock = self.map.to_block_pos(*self.pos)
        offset = [0, 0]
        mag = max(self.look_dir, key=abs)
        # get if looking towards y
        vertical = self.look_dir.index(mag)
        offset[vertical] += sign(mag)
        front_block = vec_add(pblock, offset)
        front = self.map.raw[front_block[1]][front_block[0]]
        return tuple(front_block), front

    def hits_actor(self, actor: Actor, sw):
        if (sp_sw := actor.current_sp.screen_width) is None:
            return False
        htol = sp_sw+5
        return htol > actor.hitpos(sw) > -htol

    def occupied_forthis(self, block_pos):
        return self.map.cell_occupied(block_pos) or \
            block_pos in self.map.actor_lookup

    def regain_health(self, aid):
        self.health = min(self.health + aid, 100)

    def dec_health(self, dmg):
        self.health = max(self.health - dmg, 0)

    def get_money(self):
        self.score += 500

    def get_ammo(self):
        if self.out_of_ammo():
            self.switch_weapon(self.best_weapon())
        self.ammo += 5

    def dec_ammo(self):
        self.ammo = max(self.ammo - 1, 0)
        
    def best_weapon(self):
        return max(self.acquired_weapons, key=lambda w: w.value)

    def is_new_weapon(self, weap: WolfWeapon):
        better = weap.value > self.best_weapon().value
        return better

    def acquire_weapon(self, weap: WolfWeapon):
        self.get_ammo()
        if self.is_new_weapon(weap):
            self.excited_to_kill_nazis = True
            self.switch_weapon(weap)
        self.acquired_weapons.add(weap)
        return self.excited_to_kill_nazis

    def switch_weapon(self, new: WolfWeapon):
        self.weapon = new

    def has_knife(self):
        return self.weapon == WolfWeapon.KNIFE

    def is_dead(self):
        return self.health == 0

    def reset(self):
        self.health = 100
        self.pos = self.map.init_pos.copy()
        self.update_look_dir(self.map.init_look)
        self.update_directions()
        self.weapon = WolfWeapon.PISTOL
        self.ammo = 10
        self.shooting = False
        self.acquired_weapons = set(
            [WolfWeapon.PISTOL, WolfWeapon.KNIFE, self.weapon])
        self.has_silver_key = False
        self.has_gold_key = False
        
        self.running = False

    def _1up(self):
        self.lives = (self.lives + 1) % 10

    def turn_to_killer(self, game_ctx, killer: Actor, master_surf, update_dest):
        to_killer = vec_norm(vec_sub(self.pos, killer.pos))
        angle_diff = degrees(acos(vec_dot(to_killer, self.look_dir)))
        da = sign(vec_dot(self.left, to_killer)) * 2
        while angle_diff > 2:
            self.rotate(da)
            angle_diff = degrees(acos(vec_dot(to_killer, self.look_dir)))
            game_ctx.game_renderer.render(1, game_ctx, weapon=False)
            master_surf.blit(
                game_ctx.game_renderer.pgsurface, update_dest)
            pygame.display.flip()
