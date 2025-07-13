# -*- coding: utf-8 -*-
import math
import random
from pgzero.builtins import Actor, keyboard, keys, music, images
from pygame import Rect

# --- Tile size and screen ---
TILE_W, TILE_H = 32, 32
WIDTH, HEIGHT = 800, 13 * TILE_H

# --- Map indices ---
TERRAIN_INDEX = {'W': 20, 'F': 12, ' ': -1}
DECOR_INDEX = {'P': 20}

# --- Physics constants ---
GRAVITY = 0.3
WALK_SPEED = 2
JUMP_SPEED = -10.0
ENEMY_SPEED = 1

# --- Animation frames ---
IDLE_FRAMES = [f'hero_idle_{i}' for i in range(4)]
RUN_FRAMES_R = [f'hero_run_{i}' for i in range(1, 8)]
RUN_FRAMES_L = [f'hero_run_{i}_invertido' for i in range(1, 8)]
JUMP_FRAMES = [f'hero_jump_{i}' for i in range(1, 4)]
HERO_DEATH_FRAMES = [f'hero_death_{i}' for i in range(1, 5)]

ENEMY_FRAMES_R = [f'male_walk_{i}' for i in range(1, 8)]
ENEMY_FRAMES_L = [f'male_walk_invertido_{i}' for i in range(1, 8)]
ZOMBIE_DEATH_FRAMES = [f'male_death_{i}' for i in range(1, 5)]

ENEMY2_FRAMES_R = [f'female_walk_{i}' for i in range(1, 8)]
ENEMY2_FRAMES_L = [f'female_walk_invertido_{i}' for i in range(1, 8)]
ZOMBIE2_DEATH_FRAMES = [f'female_death_{i}' for i in range(1, 5)]

# --- Animation delays ---
FRAME_DELAY = 6
IDLE_FRAME_DELAY = 60
DEATH_FRAME_DELAY = 12
ENEMY_FRAME_DELAY = 6

# --- UI buttons ---
button_start_music    = Rect((WIDTH//2-200, HEIGHT//2-80),  (400,60))
button_start_no_music = Rect((WIDTH//2-200, HEIGHT//2-10),  (400,60))
button_quit           = Rect((WIDTH//2-200, HEIGHT//2+60),  (400,60))

# --- Collision helpers ---
def is_solid_at(px, py, map_data):
    tx, ty = int(px//TILE_W), int(py//TILE_H)
    return (0 <= tx < len(map_data[0]) and 0 <= ty < len(map_data)
            and map_data[ty][tx] in {20,12})

def collides_horiz(actor, dx, map_data):
    new_x = actor.actor.x + dx
    y1 = actor.actor.y - actor.actor.height/2 + 1
    y2 = actor.actor.y + actor.actor.height/2 - 1
    for ox in (0, actor.actor.width-1):
        if is_solid_at(new_x - actor.actor.width/2 + ox, y1, map_data) or \
           is_solid_at(new_x - actor.actor.width/2 + ox, y2, map_data):
            return True
    return False

def collides_vert(actor, dy, map_data):
    new_y = actor.actor.y + dy
    x1 = actor.actor.x - actor.actor.width/2 + 1
    x2 = actor.actor.x + actor.actor.width/2 - 1
    for oy in (0, actor.actor.height-1):
        if is_solid_at(x1, new_y - actor.actor.height/2 + oy, map_data) or \
           is_solid_at(x2, new_y - actor.actor.height/2 + oy, map_data):
            return True
    return False

# --- Base entity class ---
class AnimatedEntity:
    def __init__(self, frames, death_frames, pos, speed=0, jump_speed=0, name=None):
        self.frames = frames
        self.death_frames = death_frames
        self.state = 'alive'
        self.frame_index = 0
        self.frame_counter = 0
        self.actor = Actor(self.frames['idle'][0], pos)
        self.vx = 0
        self.vy = 0
        self.speed = speed
        self.jump_speed = jump_speed
        self.current_frames = self.frames['idle']
        self.name = name

    def update_animation(self, delay):
        self.frame_counter += 1
        if self.frame_counter < delay:
            return
        self.frame_counter = 0
        self.frame_index += 1
        if self.state == 'dying':
            if self.frame_index < len(self.death_frames):
                self.actor.image = self.death_frames[self.frame_index]
            else:
                if self.name:
                    globals()[self.name] = None
                return
        else:
            self.frame_index %= len(self.current_frames)
            self.actor.image = self.current_frames[self.frame_index]

    def draw(self):
        self.actor.draw()

# --- Player class ---
class Player(AnimatedEntity):
    def __init__(self, pos):
        frames = {
            'idle': IDLE_FRAMES,
            'run_r': RUN_FRAMES_R,
            'run_l': RUN_FRAMES_L,
            'jump': JUMP_FRAMES
        }
        super().__init__(frames, HERO_DEATH_FRAMES, pos, WALK_SPEED, JUMP_SPEED)

    def is_grounded(self, map_data):
        return collides_vert(self, 1, map_data)

    def update(self, map_data):
        if self.state == 'dying':
            self.update_animation(DEATH_FRAME_DELAY)
            globals()['game_state'] = 'gameover'
            return

        if self.vx and not collides_horiz(self, self.vx, map_data):
            self.actor.x += self.vx
        else:
            self.vx = 0

        self.vy += GRAVITY
        if not collides_vert(self, self.vy, map_data):
            self.actor.y += self.vy
        else:
            self.vy = 0

        if self.vy != 0:
            key, delay = 'jump', FRAME_DELAY
        elif self.vx > 0:
            key, delay = 'run_r', FRAME_DELAY
        elif self.vx < 0:
            key, delay = 'run_l', FRAME_DELAY
        else:
            key, delay = 'idle', IDLE_FRAME_DELAY

        if self.current_frames != self.frames[key]:
            self.current_frames = self.frames[key]
            self.frame_index = self.frame_counter = 0
            self.actor.image = self.current_frames[0]
        self.update_animation(delay)

# --- Enemy class ---
class Enemy(AnimatedEntity):
    def __init__(self, name, pos, fr, fl, death):
        frames = {'walk_r': fr, 'walk_l': fl, 'idle': [fr[0]]}
        super().__init__(frames, death, pos, ENEMY_SPEED, 0, name)
        self.current_frames = frames['walk_r']
        self.vx = ENEMY_SPEED

    def update(self, map_data):
        if self.state == 'dying':
            self.update_animation(DEATH_FRAME_DELAY)
            return
        if not collides_horiz(self, self.vx, map_data):
            self.actor.x += self.vx
        else:
            self.vx *= -1
            key = 'walk_r' if self.vx > 0 else 'walk_l'
            self.current_frames = self.frames[key]
            self.frame_index = self.frame_counter = 0
            self.actor.image = self.current_frames[0]
        self.update_animation(ENEMY_FRAME_DELAY)

# --- Game globals ---
map_data = []
decor_data = []
hero = None
enemy1 = None
enemy2 = None
game_state = 'menu'
music_on = True

# --- Map loading ---
def load_map():
    global map_data, decor_data
    map_data.clear(); decor_data.clear()
    with open('map.txt') as f:
        for line in f:
            row = line.rstrip('\n')
            map_data.append([TERRAIN_INDEX.get(c,-1) for c in row])
            decor_data.append([DECOR_INDEX.get(c,-1) for c in row])
load_map()
MAP_ROWS = len(map_data)
MAP_COLS = len(map_data[0]) if MAP_ROWS else 0

# --- Tiles slicing ---
def slice_sheet(sheet):
    t = []
    for r in range(sheet.get_height()//TILE_H):
        for c in range(sheet.get_width()//TILE_W):
            t.append(sheet.subsurface(c*TILE_W, r*TILE_H, TILE_W, TILE_H))
    return t

def ensure_tiles():
    global terrain_tiles, decor_tiles
    if 'terrain_tiles' not in globals():
        globals()['terrain_tiles'] = slice_sheet(images.terrain)
        globals()['decor_tiles']   = slice_sheet(images.decorations)

# --- Spawn entities ---
def spawn_entities():
    global hero, enemy1, enemy2
    hero = Player((360, 170))
    enemy1 = Enemy('enemy1', (70, 320), ENEMY_FRAMES_R, ENEMY_FRAMES_L, ZOMBIE_DEATH_FRAMES)
    enemy2 = Enemy('enemy2', (550, 320), ENEMY2_FRAMES_R, ENEMY2_FRAMES_L, ZOMBIE2_DEATH_FRAMES)

# --- Draw ---
def draw():
    screen.clear()
    if game_state == 'menu':
        screen.draw.text('Comecar (Com Musica)', center=button_start_music.center, fontsize=40, color='white')
        screen.draw.text('Comecar (Sem Musica)', center=button_start_no_music.center, fontsize=40, color='white')
        screen.draw.text('Sair', center=button_quit.center, fontsize=40, color='white')
    elif game_state == 'playing':
        ensure_tiles()
        screen.fill('#70ABAF')
        for r in range(MAP_ROWS):
            for c in range(MAP_COLS):
                t = map_data[r][c]
                d = decor_data[r][c]
                if t >= 0:
                    screen.blit(terrain_tiles[t], (c*TILE_W, r*TILE_H))
                if d >= 0:
                    screen.blit(decor_tiles[d], (c*TILE_W, r*TILE_H))
        for ent in (hero, enemy1, enemy2):
            if ent:
                ent.draw()
    elif game_state == 'gameover':
        screen.clear()
        screen.draw.text('Game Over', center=(WIDTH/2, HEIGHT/2), fontsize=60, color='red')
    elif game_state == 'victory':
        screen.clear()
        screen.draw.text(' venceu!', center=(WIDTH/2, HEIGHT/2), fontsize=60, color='green')

# --- Update ---
def update():
    global game_state
    if game_state == 'playing':
        for ent in (hero, enemy1, enemy2):
            if ent:
                ent.update(map_data)
        for e in ('enemy1', 'enemy2'):
            en = globals().get(e)
            if hero and en and en.state == 'alive' and hero.actor.colliderect(en.actor):
                if hero.vy > 0 and hero.actor.y < en.actor.y:
                    en.state = 'dying'
                    en.frame_index = en.frame_counter = 0
                    hero.vy = hero.jump_speed / 2
                else:
                    hero.state = 'dying'
                    hero.frame_index = hero.frame_counter = 0
        if not enemy1 and not enemy2:
            game_state = 'victory'

# --- Input ---
def on_mouse_down(pos, button):
    global game_state, music_on
    if game_state == 'menu' and button == 1:
        if button_start_music.collidepoint(pos):
            music_on = True
            music.play('musica_fundo')
        elif button_start_no_music.collidepoint(pos):
            music_on = False
        elif button_quit.collidepoint(pos):
            exit()
        game_state = 'playing'
        spawn_entities()

def on_key_down(key):
    if game_state == 'playing' and hero and hero.state == 'alive':
        if key == keys.LEFT:
            hero.vx = -hero.speed
        elif key == keys.RIGHT:
            hero.vx = hero.speed
        elif key == keys.SPACE and hero.is_grounded(map_data):
            hero.vy = hero.jump_speed
        elif key == keys.M:
            if music_on:
                music.pause()
            else:
                music.unpause()
            music_on = not music_on

def on_key_up(key):
    if game_state == 'playing' and hero and hero.state == 'alive' and key in (keys.LEFT, keys.RIGHT):
        hero.vx = 0

# --- Runner ---
if __name__ == '__main__':
    import sys
    sys.argv = ['main.py', 'main.py']
    from pgzero.runner import main as _run
    _run()
