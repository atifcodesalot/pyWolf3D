

from raycaster.raycaster import Observer
from .game_objects import WolfWeapon
from .maps import WolfMap
from raycaster.aux_math import *
from .actors import Actor


class WolfPlayer(Observer):
    def __init__(self, map_: WolfMap, fov=60,
                 ray_count=256, health=100, weapon=WolfWeapon.PISTOL, ammo=20):
        super().__init__(map_.init_pos, map_.init_look, fov, ray_count)
        self.map = map_
        self.health = health
        self.weapon = weapon
        self.pace = 1.5
        self.rot_pace = 3
        self.ammo = ammo
        
        
        self.score = 0

        self.shooting = False

    def has_automatic_weapon(self):
        return self.weapon.value > 1

    def move_forward(self):
        self.displace(plain_mul(self.look_dir, self.pace))

    def move_backward(self):
        self.displace(disp=plain_mul(self.look_dir, -self.pace*1.2))

    # collide with occupied cells
    def displace(self, disp):
        new_pos = plain_add(self.pos, plain_mul(disp, 4))
        if self.map.cell_occupied(new_pos):
            # wolflogger.debug(f"Can't displace to {new_pos}")
            return
        self.translate(disp)

    def turn_cc(self):
        self.rotate(self.rot_pace)

    def turn_cw(self):
        self.rotate(-self.rot_pace)

    def out_of_ammo(self):
        return self.ammo == 0

    def get_current_cell(self):
        block_pos = self.get_current_block()
        return self.map.get_cell(block_pos)

    def get_current_block(self):
        return self.map.to_block_pos(*self.pos)

    def get_front_cell(self):
        pblock = self.map.to_block_pos(*self.pos)
        offset = [0, 0]
        mag = max(self.look_dir, key=abs)
        # get if looking towards y
        vertical = self.look_dir.index(mag)
        offset[vertical] += sign(mag)
        front_block = plain_add(pblock, offset)
        front = self.map.raw[front_block[1]][front_block[0]]
        return front_block, front

    def hit_damage(self, actor: Actor):
        pblock = self.map.to_block_pos(*self.pos)
        ablock = self.map.to_block_pos(*actor.pos)
        d = euclidean_distance(pblock, ablock)
        d = 1 if d == 0 else d
        inflicted = (1 / d) * 175
        # cap to 100
        return min(inflicted, 100)

    def hits_actor(self, raycaster, actor: Actor):
        visited = raycaster.get_corridor(*self.look_dir)
        actor_block = self.map.to_block_pos(*actor.pos)
        return actor_block in visited
    
    def regain_health(self, aid):
        self.health = min(self.health + aid, 100)
        
    def get_money(self):
        self.score += 500
        
    def get_ammo(self):
        self.ammo += 5
        
    def switch_weapon(self, new: WolfWeapon):
        self.weapon = new
