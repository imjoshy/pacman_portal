"""
        Application:    Pac-Man Portal
          File Name:    game.py
             Course:    CS 386 Into to Game Design and Production
           Semester:    Spring 20'
           Due Date:    March 11
            Authors:    David Guido   |  Contact: davidguido@litlabproductions.com
                        Josh Maranan  |  Contact:
"""

from graph import Graph
from timer import *
from sprite_store import SpriteStore
from enemy import Enemy
from pacman import Pacman
from portal import Portal
from background import Background
from pygame.sprite import Group
from os import path
import pygame as pg
import sys
import copy
import logging


# Single instance, runtime controller class
class Game:

    WIDTH = 450     # Width of game window
    HEIGHT = 600    # Height of game window

    HS_FILE = 'images/high_score.txt'

    # Initialize (Game) class
    def __init__(self):

        self.dir = path.dirname(__file__)
        pg.init()                                                       # Initialize pygame
        self.BG_COLOR = (0, 0, 0)                                       # Set background to black
        self.screen = pg.display.set_mode((Game.WIDTH, Game.HEIGHT))    # Set window dimensions
        pg.display.set_caption('Pac-Man')                               # Set name of the game

        # ******************
        # *** Animations ***
        # ******************
        self.CLOCK = pg.time.Clock()                                        # Universal animation clock

        self.img_index = Timer(3)                                           # Pac-man Animations
        self.last_img_index = self.img_index.frame_index()

        self.enemy_img_index = Timer(2)                                     # Enemy Animations
        self.last_enemy_img_index = self.enemy_img_index.frame_index()
        self.enemy_scatter_index = TimerDual(2, 4)

        self.sprite_store = SpriteStore()                                   # Instance for retrieving sprites

        portal_sprites = []                                                 # Portal Animations
        for sprite in self.sprite_store.portal:                             # Fill list with unscaled images
            portal_sprites.append(pg.transform.scale(sprite, (20, 20)))

        self.portal_img_index = Timer(6)

        # ********************
        # *** Game Objects ***
        # ********************
        self.graph = Graph(self)    # Graph (Map) obj

        self.pacman = Pacman(self, self.sprite_store.pacman, self.graph)     # Pac-man obj

        self.portal1 = Portal(self, portal_sprites)      # Portal One obj
        self.portal2 = Portal(self, portal_sprites)      # Portal Two obj
        self.portals = [self.portal1, self.portal2]      # List of Portal obj's

        self.blinky_scatter_nodes = [self.graph.nodes[4], self.graph.nodes[5], self.graph.nodes[13],
                                     self.graph.nodes[12]]
        self.pinky_scatter_nodes = [self.graph.nodes[0], self.graph.nodes[6], self.graph.nodes[7], self.graph.nodes[1]]
        self.clyde_scatter_nodes = [self.graph.nodes[42], self.graph.nodes[43], self.graph.nodes[53],
                                    self.graph.nodes[54],
                                    self.graph.nodes[61], self.graph.nodes[60], self.graph.nodes[50],
                                    self.graph.nodes[51], self.graph.nodes[52]]

        self.inkey_scatter_nodes = [self.graph.nodes[46], self.graph.nodes[47], self.graph.nodes[57],
                                    self.graph.nodes[58],
                                    self.graph.nodes[59], self.graph.nodes[63], self.graph.nodes[62],
                                    self.graph.nodes[55], self.graph.nodes[56]]

        # 1. Blinky obj (Enemy00)
        self.blinky = Enemy(self, self.sprite_store.blinky, self.graph, self.blinky_scatter_nodes)
        # 2. Pinky  obj (Enemy01)
        self.pinky = Enemy(self, self.sprite_store.pinky, self.graph, self.pinky_scatter_nodes)
        # 3. Clyde  obj (Enemy02)
        self.clyde = Enemy(self, self.sprite_store.clyde, self.graph, self.clyde_scatter_nodes)
        # 4. Inkey  obj (Enemy03)
        self.inkey = Enemy(self, self.sprite_store.inkey, self.graph, self.inkey_scatter_nodes)

        self.enemies = []                                                   # List of Enemy obj's
        self.enemies.append(self.blinky)                                    # Add enemies to list
        self.enemies.append(self.pinky)
        self.enemies.append(self.clyde)
        self.enemies.append(self.inkey)

        self.bg = Background('images/map.png', (0, 60))  # Background Image obj
        self.small_logo = self.sprite_store.get_small_logo()
        self.big_logo = self.sprite_store.get_bigger_logo()
        # **********************
        # *** Initialization ***
        # **********************
        self.pacman.rect.centerx = self.graph.nodes[65].x            # Set Pac-man to node 65
        self.pacman.rect.centery = self.graph.nodes[65].y
        self.pacman.adj_node = self.graph.nodes[65]

        self.initialize_enemies()

        self.pellets = Group()

        for pellet in self.graph.pellets:
            self.pellets.add(pellet)

        self.score = 0
        self.high_score = 0
        self.win = False
        self.last_key = None    # Last key the user inputted

        self.start_screen = True

        self.initial_start = True
        self.is_paused = False
        self.game_over = False
        self.new_life = False
        self.has_game_started = False

        # buttons
        self.play_button = True
        self.play_button_rect = None
        self.hs_show = False
        self.hs_button = True
        self.hs_button_rect = None
        self.back_button = False
        self.back_button_rect = None

        self.last_flip = pg.time.get_ticks()
        self.show = True

        # define the RGB value for white,
        #  green, blue colour .
        self.white = (255, 255, 255)
        self.green = (0, 255, 0)
        self.blue = (0, 0, 128)

        # ************************
        # ********* U.I. *********
        # ************************
        self.pac_life_icon = self.sprite_store.pac_life
        self.cherry_icon = self.sprite_store.fruits[0]
        self.sound_icon = pg.image.load(r'images/sound_icon.png')

        self.load_high_score()   # Load high scores
        # ************************
        # ******** Sounds ********
        # ************************
        pg.mixer.init()

        # If you want more channels, change 8 to a desired number. 8 is the default number of channel

        pg.mixer.set_num_channels(8)
        self.voice = pg.mixer.Channel(5)
        self.portal = pg.mixer.Channel(6)

        # This is the sound channel
        self.eating_sound = pg.mixer.Sound('sounds/chomp.wav')
        self.death_sound = pg.mixer.Sound('sounds/pacman_death.wav')
        self.beginning_music = pg.mixer.Sound('sounds/beginning.wav')
        self.portal_shoot = pg.mixer.Sound('sounds/portal_shoot.wav')
        self.tp_sound = pg.mixer.Sound('sounds/tp.wav')
        self.eat_ghost_sound = pg.mixer.Sound('sounds/pacman_eat_ghost.wav')
        pg.mixer.music.load('sounds/pkmn_trainer_victory_cut_for_loop.wav')

        spac_imgs = self.sprite_store.get_pacman_sprites()      # L indices -- 0, 1, 2 // R indices -- 0, 3, 4
        self.starter_pacman = []
        for img in spac_imgs:
            self.starter_pacman.append(pg.transform.scale(img, (48, 48)))
        self.starter_pacman_rect = self.starter_pacman[0].get_rect()
        self.starter_pacman_rect.centerx = -48
        self.starter_pacman_rect.centery = 430

        # ALL GHOSTS: L indices -- 4, 5 // R indices -- 0, 1
        sblinky_imgs = self.sprite_store.get_blinky_sprites()
        self.starter_blinky = []
        for img in sblinky_imgs:
            self.starter_blinky.append(pg.transform.scale(img, (48, 48)))
        self.starter_blinky_rect = self.starter_blinky[0].get_rect()
        self.starter_blinky_rect.centerx = -144
        self.starter_blinky_rect.centery = 430

        spinky_imgs = self.sprite_store.get_pinky_sprites()
        self.starter_pinky = []
        for img in spinky_imgs:
            self.starter_pinky.append(pg.transform.scale(img, (48, 48)))
        self.starter_pinky_rect = self.starter_pinky[0].get_rect()
        self.starter_pinky_rect.centerx = -199
        self.starter_pinky_rect.centery = 430

        sclyde_imgs = self.sprite_store.get_clyde_sprites()
        self.starter_clyde = []
        for img in sclyde_imgs:
            self.starter_clyde.append(pg.transform.scale(img, (48, 48)))
        self.starter_clyde_rect = self.starter_clyde[0].get_rect()
        self.starter_clyde_rect.centerx = -254
        self.starter_clyde_rect.centery = 430

        sinkey_imgs = self.sprite_store.get_inkey_sprites()
        self.starter_inkey = []
        for img in sinkey_imgs:
            self.starter_inkey.append(pg.transform.scale(img, (48, 48)))
        self.starter_inkey_rect = self.starter_inkey[0].get_rect()
        self.starter_inkey_rect.centerx = -309
        self.starter_inkey_rect.centery = 430

        running_away = self.sprite_store.get_ghost_running_away_sprites()
        self.starter_running_away = []
        for img in running_away:
            self.starter_running_away.append(pg.transform.scale(img, (48, 48)))

        self.starter_entities = []
        self.starter_entities.append([self.starter_blinky, self.starter_blinky_rect])
        self.starter_entities.append([self.starter_pinky, self.starter_pinky_rect])
        self.starter_entities.append([self.starter_clyde, self.starter_clyde_rect])
        self.starter_entities.append([self.starter_inkey, self.starter_inkey_rect])

        self.starter_right = True

        self.start_ticks = pg.time.get_ticks()
        self.inkey_ticks = pg.time.get_ticks()
        self.pinky_ticks = pg.time.get_ticks()
        self.clyde_ticks = pg.time.get_ticks()
        self.blinky_ticks = pg.time.get_ticks()

        self.seconds = 0
        self.blinky_mode_seconds = 0
        self.inkey_mode_seconds = 0
        self.pinky_mode_seconds = 0
        self.clyde_mode_seconds = 0

    def load_high_score(self):
        # load high score
        with open(path.join(self.dir, self.HS_FILE), 'r') as f:
            try:
                self.high_score = int(f.read())
            except Exception as e:      # required, else "too broad exception clause
                logging.exception(e)
                self.high_score = 0

    def display_sprites(self):
        # DIRECTION INDICES
        # for pacman
        pr_ind = (0, 3, 4)
        pl_ind = (0, 1, 2)
        # for ghosts
        l_running_ind = (2, 3)
        gr_ind = (0, 1)

        if self.starter_pacman_rect.right < -200:
            self.starter_right = True       # go right because too far left
            self.starter_pacman_rect.centerx = -48
            self.starter_blinky_rect.centerx = -144
            self.starter_pinky_rect.centerx = -199
            self.starter_clyde_rect.centerx = -254
            self.starter_inkey_rect.centerx = -309
        if self.starter_inkey_rect.left >= (self.WIDTH + 200):
            self.starter_right = False      # go left because too far right
            self.starter_inkey_rect.centerx = self.WIDTH + 48
            self.starter_clyde_rect.centerx = self.WIDTH + 103
            self.starter_pinky_rect.centerx = self.WIDTH + 158
            self.starter_blinky_rect.centerx = self.WIDTH + 213
            self.starter_pacman_rect.centerx = self.WIDTH + 309

        if self.starter_right:
            self.screen.blit(self.starter_pacman[pr_ind[self.img_index.frame_index()]], self.starter_pacman_rect)
            for entity in self.starter_entities:
                self.screen.blit(entity[0][gr_ind[self.enemy_img_index.frame_index()]], entity[1])

            self.starter_pacman_rect.centerx += 2
            for entity in self.starter_entities:
                entity[1].centerx += 2
        if not self.starter_right:
            self.screen.blit(self.starter_pacman[pl_ind[self.img_index.frame_index()]], self.starter_pacman_rect)
            for entity in self.starter_entities:
                self.screen.blit(self.starter_running_away[l_running_ind[self.enemy_img_index.frame_index()]],
                                 entity[1])

            self.starter_pacman_rect.centerx -= 2
            for entity in self.starter_entities:
                entity[1].centerx -= 2

    def display_introduction(self):
        gr_ind = (0, 1)

        font = pg.font.Font('Gameplay.ttf', 20)

        # blinky
        bimg_rect = copy.deepcopy(self.starter_blinky_rect)
        bimg_rect.centerx = 170
        bimg_rect.centery = 245

        blinky_text = font.render('Blinky', True, (255, 0, 0))      # 255 0 0 -- red
        btext_rect = blinky_text.get_rect()
        btext_rect.centerx = bimg_rect.left - 50
        btext_rect.centery = bimg_rect.centery

        self.screen.blit(self.starter_blinky[gr_ind[self.enemy_img_index.frame_index()]], bimg_rect)
        self.screen.blit(blinky_text, btext_rect)

        # pinky
        pimg_rect = copy.deepcopy(self.starter_pinky_rect)
        pimg_rect.centerx = 281
        pimg_rect.centery = 245

        pinky_text = font.render('Pinky', True, (255, 153, 255))      # 255 153 255 -- pink
        ptext_rect = pinky_text.get_rect()
        ptext_rect.centerx = pimg_rect.right + 50
        ptext_rect.centery = pimg_rect.centery

        self.screen.blit(self.starter_pinky[gr_ind[self.enemy_img_index.frame_index()]], pimg_rect)
        self.screen.blit(pinky_text, ptext_rect)
        # clyde
        cimg_rect = copy.deepcopy(self.starter_clyde_rect)
        cimg_rect.centerx = 170
        cimg_rect.centery = 320

        clyde_text = font.render('Clyde', True, (255, 204, 0))      # 255 204, 0 -- clyde color
        ctext_rect = clyde_text.get_rect()
        ctext_rect.centerx = cimg_rect.left - 50
        ctext_rect.centery = cimg_rect.centery

        self.screen.blit(self.starter_clyde[gr_ind[self.enemy_img_index.frame_index()]], cimg_rect)
        self.screen.blit(clyde_text, ctext_rect)
        # inky
        iimg_rect = copy.deepcopy(self.starter_pinky_rect)
        iimg_rect.centerx = 281
        iimg_rect.centery = 320

        inkey_text = font.render('Inkey', True, (0, 255, 255))      # 0 255 255 -- inkey color
        itext_rect = inkey_text.get_rect()
        itext_rect.centerx = iimg_rect.right + 50
        itext_rect.centery = iimg_rect.centery

        self.screen.blit(self.starter_inkey[gr_ind[self.enemy_img_index.frame_index()]], iimg_rect)
        self.screen.blit(inkey_text, itext_rect)

    # Contains main game loops
    def play(self):
        pg.mixer.music.stop()
        while self.start_screen:
            flip_time = 250      # blink prompt every 500 ms
            self.process_events()   # CLICK HERE to start the game

            font = pg.font.Font('Gameplay.ttf', 25)

            play_game_prompt = font.render('PLAY', True, self.white)
            self.play_button_rect = play_game_prompt.get_rect()
            self.play_button_rect.center = ((self.WIDTH // 2), 475)

            hs_prompt = font.render('High Score', True, self.white)
            self.hs_button_rect = hs_prompt.get_rect()
            self.hs_button_rect.center = ((self.WIDTH // 2), 525)

            hs = font.render(str(self.high_score), True, self.white)
            hs_rect = self.play_button_rect

            back_prompt = font.render('Back', True, self.white)
            self.back_button_rect = back_prompt.get_rect()
            self.back_button_rect.center = ((self.WIDTH // 2), 525)

            font = pg.font.Font('Gameplay.ttf', 10)
            credit = font.render('Project by David Guido and Joshua Maranan', True, self.white)
            credit_rect = credit.get_rect()
            credit_rect.center = ((self.WIDTH // 2), (self.HEIGHT - 20))

            time_since = abs(self.last_flip - pg.time.get_ticks())
            if time_since >= flip_time:
                self.show = not self.show
                self.last_flip = pg.time.get_ticks()

            self.screen.fill(self.BG_COLOR)  # Set background color to black
            self.display_sprites()
            self.display_introduction()
            self.screen.blit(self.big_logo, (0, 0))     # w = 450, h = 200
            if self.show and self.play_button:
                self.screen.blit(play_game_prompt, self.play_button_rect)
            if self.hs_button:
                self.screen.blit(hs_prompt, self.hs_button_rect)
            if self.back_button:
                self.screen.blit(back_prompt, self.back_button_rect)
            if self.hs_show:
                self.screen.blit(hs, hs_rect)

            self.screen.blit(credit, credit_rect)

            pg.display.update()

        self.beginning_music.play()

        self.start_ticks = pg.time.get_ticks()
        while not self.has_game_started:

            # Game timer 00
            self.seconds = (pg.time.get_ticks() - self.start_ticks) / 1000  # calculate how many seconds
            if self.seconds > 5.5:  # if more than 10 seconds close the game
                self.has_game_started = True
                self.initial_start = False

            self.blinky.current_state = 'scattered'
            self.pinky.current_state = 'scattered'
            self.clyde.current_state = 'scattered'
            self.inkey.current_state = 'scattered'

            self.process_events()                   # Get user input
            self.update()                           # Update this (Game) instance
            self.graph.update()                     # Update (Graph) instance
            self.pacman.update()                    # Update (Pac-man) instance
            self.ui_update()

            for enemy in self.enemies:              # Update (Enemy) instances
                enemy.update()

            pg.display.update()  # Tell game engine to update this games display

        while not self.win and not self.game_over \
                and not self.is_paused and not self.new_life:

            self.blinky_mode_seconds = (pg.time.get_ticks() - self.blinky_ticks) / 1000
            self.inkey_mode_seconds = (pg.time.get_ticks() - self.inkey_ticks) / 1000
            self.pinky_mode_seconds = (pg.time.get_ticks() - self.pinky_ticks) / 1000
            self.clyde_mode_seconds = (pg.time.get_ticks() - self.clyde_ticks) / 1000

            self.blinky.has_enemy_exited_room = True

            # Power pellets
            if self.pacman.op:
                self.blinky.current_state = 'frightened'
                self.pinky.current_state = 'frightened'
                self.clyde.current_state = 'frightened'
                self.inkey.current_state = 'frightened'
                self.inkey_ticks = pg.time.get_ticks()
                self.pinky_ticks = pg.time.get_ticks()
                self.clyde_ticks = pg.time.get_ticks()
                self.blinky_ticks = pg.time.get_ticks()

            # Switch between scatter and chase
            else:

                # Blinky
                if len(self.graph.get_map_buffer(self.blinky, self.blinky.direction)) > 0:
                    collide_point_x = self.graph.get_map_buffer(self.blinky, self.blinky.direction)[0]
                    collide_point_y = self.graph.get_map_buffer(self.blinky, self.blinky.direction)[1]
                else:
                    collide_point_x = 0
                    collide_point_y = 0

                if self.blinky.rect.collidepoint(collide_point_x, collide_point_y):

                    if self.blinky.go_home:
                        self.blinky.current_state = 'return'
                    elif self.blinky.current_state == 'return' and not self.pacman.op:
                        self.blinky.current_state = 'scatter'
                    elif self.blinky.current_state == 'frightened':
                        self.blinky.current_state = 'chase'

                    elif self.blinky_mode_seconds > 30:
                        if self.blinky.current_state == 'chase':

                            # Change to scatter state
                            self.blinky.current_state = 'scattered'

                            # Reset time
                            self.blinky_ticks = pg.time.get_ticks()

                        elif self.blinky.current_state == 'scattered':
                            self.blinky.current_state = 'chase'
                            self.blinky_ticks = pg.time.get_ticks()

                # Pinky
                if self.pinky_mode_seconds > 6:
                    self.pinky.has_enemy_exited_room = True

                if len(self.graph.get_map_buffer(self.pinky, self.pinky.direction)) > 0:
                    collide_point_x = self.graph.get_map_buffer(self.pinky, self.pinky.direction)[0]
                    collide_point_y = self.graph.get_map_buffer(self.pinky, self.pinky.direction)[1]
                else:
                    collide_point_x = 0
                    collide_point_y = 0

                if self.pinky.rect.collidepoint(collide_point_x, collide_point_y):

                    if self.pinky.go_home:
                        self.pinky.current_state = 'return'
                    elif self.pinky.current_state == 'return' and not self.pacman.op:
                        self.pinky.current_state = 'scatter'
                    elif self.pinky.current_state == 'frightened':
                        self.pinky.current_state = 'chase'

                    elif self.pinky_mode_seconds > 30:
                        if self.pinky.current_state == 'chase':

                            # Change to scatter state
                            self.pinky.current_state = 'scattered'

                            # Reset time
                            self.pinky_ticks = pg.time.get_ticks()

                        elif self.pinky.current_state == 'scattered':
                            self.pinky.current_state = 'chase'
                            self.pinky_ticks = pg.time.get_ticks()

                # Clyde
                if self.clyde_mode_seconds > 8:
                    self.clyde.has_enemy_exited_room = True

                if len(self.graph.get_map_buffer(self.clyde, self.clyde.direction)) > 0:
                    collide_point_x = self.graph.get_map_buffer(self.clyde, self.clyde.direction)[0]
                    collide_point_y = self.graph.get_map_buffer(self.clyde, self.clyde.direction)[1]
                else:
                    collide_point_x = 0
                    collide_point_y = 0

                if self.clyde.rect.collidepoint(collide_point_x, collide_point_y):

                    if self.clyde.go_home:
                        self.clyde.current_state = 'return'
                    elif self.clyde.current_state == 'return' and not self.pacman.op:
                        self.clyde.current_state = 'scatter'
                    elif self.clyde.current_state == 'frightened':
                        self.clyde.current_state = 'chase'

                    elif self.clyde_mode_seconds > 30:
                        if self.clyde.current_state == 'chase':

                            # Change to scatter state
                            self.clyde.current_state = 'scattered'

                            # Reset time
                            self.clyde_ticks = pg.time.get_ticks()

                        elif self.clyde.current_state == 'scattered':
                            self.clyde.current_state = 'chase'
                            self.clyde_ticks = pg.time.get_ticks()

                # Inkey
                if self.inkey_mode_seconds > 10:
                    self.inkey.has_enemy_exited_room = True

                if len(self.graph.get_map_buffer(self.inkey, self.inkey.direction)) > 0:
                    collide_point_x = self.graph.get_map_buffer(self.inkey, self.inkey.direction)[0]
                    collide_point_y = self.graph.get_map_buffer(self.inkey, self.inkey.direction)[1]
                else:
                    collide_point_x = 0
                    collide_point_y = 0

                if self.inkey.rect.collidepoint(collide_point_x, collide_point_y):

                    if self.inkey.go_home:
                        self.inkey.current_state = 'return'
                    elif self.inkey.current_state == 'return' and not self.pacman.op:
                        self.inkey.current_state = 'scatter'
                    elif self.inkey.current_state == 'frightened':
                        self.inkey.current_state = 'chase'

                    elif self.inkey_mode_seconds > 30:
                        if self.inkey.current_state == 'chase':

                            # Change to scatter state
                            self.inkey.current_state = 'scattered'

                            # Reset time
                            self.inkey_ticks = pg.time.get_ticks()

                        elif self.inkey.current_state == 'scattered':
                            self.inkey.current_state = 'chase'
                            self.inkey_ticks = pg.time.get_ticks()

            print('blinky mode: ' + self.blinky.current_state)
            print('pacman op: ' + str(self.pacman.op))

            print('blinky:' + str(self.blinky_mode_seconds))
            # print ('pinky:' +  str(self.pinky_mode_seconds))
            # print ('clyde:' +  str(self.clyde_mode_seconds))
            # print ('inkey: ' +  str(self.inkey_mode_seconds))

            self.process_events()           # Get user input
            self.update()                    # Update this (Game) instance

            self.graph.update()             # Update (Graph) instance

            self.pacman.update()            # Update (Pac-man) instance
            self.ui_update()
            for enemy in self.enemies:      # Update (Enemy) instances
                enemy.update()

            pg.display.update()          # Tell game engine to update this games display

            if not self.is_paused:
                self.CLOCK.tick(60)             # Limit display rate

            if self.game_over:
                self.show_game_over()
                self.beginning_music.play()
                self.play()
            elif self.new_life:
                self.reset_map()
                self.last_key = 'stop'
        if self.win:
            pg.mixer.music.play(-1)
            self.display_win()

    def display_win(self):
        # Save high score
        if self.score > self.high_score:
            self.high_score = self.score
            with open(path.join(self.dir, self.HS_FILE), 'w') as f:
                f.write(str(self.high_score))

        # Texts
        font = pg.font.Font('Gameplay.ttf', 32)
        restart_font = pg.font.Font('Gameplay.ttf', 12)

        text = font.render('You Win!', True, (205, 204, 0), self.blue)
        restart_text = restart_font.render('Press R to restart.', True, (205, 204, 0),  self.blue)

        text_rect = text.get_rect()
        restart_text_rect = restart_text.get_rect()

        text_rect.center = (self.WIDTH // 2, self.HEIGHT // 2)
        restart_text_rect.center = (self.WIDTH // 2, (self.HEIGHT // 2) + 50)

        while self.win:

            self.screen.blit(text, text_rect)
            self.screen.blit(restart_text, restart_text_rect)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_r:
                        self.__init__()
                        self.has_game_started = False
                        self.play()

            pg.display.update()
            self.CLOCK.tick(15)

    def ui_update(self):
        # Logo
        self.screen.blit(self.small_logo, (0, 0))
        # Fruit
        self.screen.blit(self.graph.fruits[self.graph.fruit_index], (self.WIDTH - 80, self.HEIGHT - 28))

        # Texts
        font = pg.font.Font('freesansbold.ttf', 16)

        high_score_label = font.render('HIGH SCORE', True, self.white)
        high_score_text = font.render(str(self.high_score), True, self.white)
        one_up_label = font.render('1UP', True, self.white)
        current_score_text = font.render(str(self.score), True, self.white)

        text_rect00 = high_score_label.get_rect()
        text_rect01 = high_score_text.get_rect()
        text_rect02 = one_up_label.get_rect()
        text_rect03 = current_score_text.get_rect()

        text_rect00.center = ((self.WIDTH // 2) - 5, 20)
        text_rect01.center = ((self.WIDTH // 2) - 5, 40)
        text_rect02.center = ((self.WIDTH // 2) + 100, 20)
        text_rect03.center = ((self.WIDTH // 2) + 100, 40)

        self.screen.blit(high_score_label, text_rect00)
        self.screen.blit(high_score_text, text_rect01)
        self.screen.blit(current_score_text, text_rect03)

        # blinking 1UP
        flip_time = 250     # blink 1UP every 250 ms
        time_since = abs(self.last_flip - pg.time.get_ticks())
        if time_since >= flip_time:
            self.show = not self.show
            self.last_flip = pg.time.get_ticks()

        if self.show:
            self.screen.blit(one_up_label, text_rect02)

        # Sound icon
        self.screen.blit(self.sound_icon, (self.WIDTH - 50, 20))

        # Pac lives
        if self.pacman.lives == 3:
            self.screen.blit(self.pac_life_icon, (10, self.HEIGHT - 28))
            self.screen.blit(self.pac_life_icon, (35, self.HEIGHT - 28))
        elif self.pacman.lives == 2:
            self.screen.blit(self.pac_life_icon, (10, self.HEIGHT - 28))

    def reinit(self):
        self.pacman = Pacman(self, self.sprite_store.pacman, self.graph)  # Pac-man obj

        self.blinky_scatter_nodes = [self.graph.nodes[4], self.graph.nodes[5],
                                     self.graph.nodes[13], self.graph.nodes[12]]

        self.pinky_scatter_nodes = [self.graph.nodes[0], self.graph.nodes[6], self.graph.nodes[7], self.graph.nodes[1]]
        self.clyde_scatter_nodes = [self.graph.nodes[42], self.graph.nodes[43], self.graph.nodes[53],
                                    self.graph.nodes[54], self.graph.nodes[61], self.graph.nodes[60],
                                    self.graph.nodes[50], self.graph.nodes[51], self.graph.nodes[52]]

        self.inkey_scatter_nodes = [self.graph.nodes[46], self.graph.nodes[47], self.graph.nodes[57],
                                    self.graph.nodes[58], self.graph.nodes[59], self.graph.nodes[63],
                                    self.graph.nodes[62], self.graph.nodes[55], self.graph.nodes[56]]

        # 1. Blinky obj (Enemy00)
        self.blinky = Enemy(self, self.sprite_store.blinky, self.graph, self.blinky_scatter_nodes)
        # 2. Pinky  obj (Enemy01)
        self.pinky = Enemy(self, self.sprite_store.pinky, self.graph, self.pinky_scatter_nodes)
        # 3. Clyde  obj (Enemy02)
        self.clyde = Enemy(self, self.sprite_store.clyde, self.graph, self.clyde_scatter_nodes)
        # 4. Inkey  obj (Enemy03)
        self.inkey = Enemy(self, self.sprite_store.inkey, self.graph, self.inkey_scatter_nodes)

        self.inkey_ticks = pg.time.get_ticks()
        self.pinky_ticks = pg.time.get_ticks()
        self.clyde_ticks = pg.time.get_ticks()
        self.blinky_ticks = pg.time.get_ticks()

        for enemy in self.enemies:
            enemy.has_enemy_exited_room = False

        self.blinky.current_state = 'scattered'
        self.pinky.current_state = 'scattered'
        self.clyde.current_state = 'scattered'
        self.inkey.current_state = 'scattered'

        self.enemies = []                                       # List of Enemy obj's
        self.enemies.append(self.blinky)  # Add enemies to list
        self.enemies.append(self.pinky)
        self.enemies.append(self.clyde)
        self.enemies.append(self.inkey)

        self.pacman.rect.centerx = self.graph.nodes[65].x  # Set Pac-man to node 65
        self.pacman.rect.centery = self.graph.nodes[65].y
        self.pacman.adj_node = self.graph.nodes[65]

        self.initialize_enemies()

    def reset_map(self):
        temp = self.pacman.lives
        self.reinit()
        self.pacman.lives = temp
        self.new_life = False
        delay = 2000    # delay is 2 seconds after resetting
        start = pg.time.get_ticks()
        while abs(start - pg.time.get_ticks()) <= delay:        # reset screen and wait 2 seconds
            self.process_events()  # Get user input
            self.update()  # Update this (Game) instance

            self.graph.update()  # Update (Graph) instance

            self.pacman.update()  # Update (Pac-man) instance
            self.ui_update()
            for enemy in self.enemies:  # Update (Enemy) instances
                enemy.update()

            pg.display.update()  # Tell game engine to update this games display
        self.has_game_started = True        # restart the game

    def show_game_over(self):
        # Save high score
        if self.score > self.high_score:
            self.high_score = self.score
            with open(path.join(self.dir, self.HS_FILE), 'w') as f:
                f.write(str(self.high_score))

        # Texts
        font = pg.font.Font('Gameplay.ttf', 32)
        restart_font = pg.font.Font('Gameplay.ttf', 12)

        text = font.render('Game Over', True, self.green, self.blue)
        restart_text = restart_font.render('Press R to restart.', True, self.green, self.blue)

        text_rect = text.get_rect()
        restart_text_rect = restart_text.get_rect()

        text_rect.center = (self.WIDTH // 2, self.HEIGHT // 2)
        restart_text_rect.center = (self.WIDTH // 2, (self.HEIGHT // 2) + 50)

        while self.game_over:

            self.screen.blit(text, text_rect)
            self.screen.blit(restart_text, restart_text_rect)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_r:
                        self.__init__()
                        self.has_game_started = False

            pg.display.update()
            self.CLOCK.tick(15)

    def un_pause(self):
        self.is_paused = False
        print('game is un-paused')

    def pause(self):
        self.is_paused = True
        print('game is paused')

        # create a font object.
        # 1st parameter is the font file
        # which is present in pygame.
        # 2nd parameter is size of the font
        font = pg.font.Font('freesansbold.ttf', 32)

        # create a text suface object,
        # on which text is drawn on it.
        text = font.render('Paused', True, self.green, self.blue)

        # create a rectangular object for the
        # text surface object
        text_rect = text.get_rect()

        # set the center of the rectangular object.
        text_rect.center = (self.WIDTH // 2, self.HEIGHT // 2)

        while self.is_paused:

            # copying the text surface object
            # to the display surface object
            # at the center coordinate.
            self.screen.blit(text, text_rect)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_p:
                        self.un_pause()

            pg.display.update()
            self.CLOCK.tick(15)

            # Set 'Last Key' to user input

    def process_events(self):

        for event in pg.event.get():
            if event.type == pg.QUIT:
                sys.exit()
            # elif event.type == pg.KEYDOWN and not self.has_game_started:      # allows for ENTER to start game
            #     if event.key == pg.K_RETURN:
            #         self.start_screen = False
            elif event.type == pg.MOUSEBUTTONDOWN and not self.has_game_started:
                x, y = event.pos
                if self.play_button_rect.collidepoint(x, y):
                    self.start_screen = False
                elif self.hs_button_rect.collidepoint(x, y) and self.hs_button:
                    self.play_button = False
                    self.hs_button = False
                    self.hs_show = True
                    self.back_button = True
                elif self.back_button_rect.collidepoint(x, y) and self.back_button:
                    self.play_button = True
                    self.hs_button = True
                    self.hs_show = False
                    self.back_button = False
            elif event.type == pg.KEYDOWN and self.has_game_started:
                if event.key == pg.K_p:
                    self.pause()
                elif event.key == pg.K_LEFT:
                    self.last_key = 'left'
                elif event.key == pg.K_RIGHT:
                    self.last_key = 'right'
                elif event.key == pg.K_UP:
                    self.last_key = 'up'
                elif event.key == pg.K_DOWN:
                    self.last_key = 'down'
                elif event.key == pg.K_z:
                    self.portal1.fire()
                elif event.key == pg.K_x:
                    self.portal2.fire()

    # Update the single (Game) instance
    def update(self):

        self.screen.fill(self.BG_COLOR)                 # Set background color to black
        self.screen.blit(self.bg.image, self.bg.rect)   # Set game background to the maze background image

        self.portal1.update()   # Update portals
        self.portal2.update()

    def initialize_enemies(self):

        self.blinky.rect.centerx = self.graph.nodes[69].x
        self.blinky.rect.centery = self.graph.nodes[69].y
        self.blinky.current_node = self.graph.nodes[69]
        self.blinky.adj_node = self.graph.nodes[24]

        shortest_path = self.graph.get_shortest_path(self.blinky.current_node, self.pacman.current_node)

        if len(shortest_path) > 0:
            self.blinky.adj_node = shortest_path[0].node
            self.blinky.next_node = shortest_path[len(shortest_path) - 1].node
            # = self.graph.get_adj_path(self.blinky.current_node, self.blinky.direction)[0]

        self.pinky.rect.centerx = self.graph.nodes[67].x
        self.pinky.rect.centery = self.graph.nodes[67].y
        self.pinky.current_node = self.graph.nodes[67]
        self.pinky.adj_node = self.graph.nodes[68]

        shortest_path = self.graph.get_shortest_path(self.pinky.current_node, self.pacman.current_node)

        if len(shortest_path) > 0:
            self.pinky.adj_node = shortest_path[0].node
            self.pinky.next_node = shortest_path[len(shortest_path) - 1].node

        self.clyde.rect.centerx = self.graph.nodes[68].x
        self.clyde.rect.centery = self.graph.nodes[68].y
        self.clyde.current_node = self.graph.nodes[68]
        self.clyde.adj_node = self.graph.nodes[67]

        shortest_path = self.graph.get_shortest_path(self.clyde.current_node, self.pacman.current_node)

        if len(shortest_path) > 0:
            self.clyde.adj_node = shortest_path[0].node
            self.clyde.next_node = shortest_path[len(shortest_path) - 1].node

        self.inkey.rect.centerx = self.graph.nodes[66].x  # Set Inkey to his special starting node
        self.inkey.rect.centery = self.graph.nodes[66].y
        self.inkey.current_node = self.graph.nodes[66]
        self.inkey.adj_node = self.graph.nodes[67]

        shortest_path = self.graph.get_shortest_path(self.inkey.current_node, self.pacman.current_node)

        if len(shortest_path) > 0:
            self.inkey.adj_node = shortest_path[0].node
            self.inkey.next_node = shortest_path[len(shortest_path) - 1].node


def main():
    game = Game()
    game.play()


if __name__ == '__main__':
    main()
