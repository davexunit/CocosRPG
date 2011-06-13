# This code is so you can run the samples without installing the package
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pyglet
from pyglet.window import key, mouse
from pyglet.gl import *

pyglet.resource.path.append(pyglet.resource.get_script_home())
pyglet.resource.reindex()

import cocos
from cocos import tiles, actions, layer, rect

class MovePlayer(actions.Move, tiles.RectMapCollider):
    def step(self, dt):
        # Potential velocity if no collision occurs
        self.dx, self.dy = (keyboard[key.D] - keyboard[key.A]) * self.target.speed, (keyboard[key.W] - keyboard[key.S]) * self.target.speed

        # Skip collision checks if the sprite isn't moving
        if self.dx != 0 or self.dy != 0:
            if self.dy > 0:
                if self.target.image != walk_north:
                    self.target.image = walk_north
                    self.target.direction = DIR_NORTH
            elif self.dy < 0:
                if self.target.image != walk_south:
                    self.target.image = walk_south
                    self.target.direction = DIR_SOUTH
            elif self.dx > 0:
                if self.target.image != walk_east:
                    self.target.image = walk_east
                    self.target.direction = DIR_EAST
            elif self.dx < 0:
                if self.target.image != walk_west:
                    self.target.image = walk_west
                    self.target.direction = DIR_WEST
            # Create rect for collision testing by translating hitbox by sprite location
            last = self.target.hitbox.copy()
            last.x += self.target.get_rect().x
            last.y += self.target.get_rect().y

            # Test for collision along x axis
            new = last.copy()
            new.x += self.dx * dt
            if self.collide_player(new):
                self.dx = 0
            else:
                self.collide_map(test_layer, last, new, None, None)

            # Test for collision along y axis
            new = last.copy()
            new.y += self.dy * dt
            if self.collide_player(new):
                self.dy = 0
            else:
                self.collide_map(test_layer, last, new, None, None)
        else:
            stop_sprite(self.target)

        # Set new velocity
        self.target.velocity = (self.dx, self.dy)

        # Move
        super(MovePlayer, self).step(dt)

        # Focus scrolling layer on player
        scroller.set_focus(self.target.x, self.target.y)
        # Y sort
        player_layer.remove(self.target)
        player_layer.add(self.target, z=-self.target.y)

    def collide_player(self, new):
        for s in player_layer.get_children():
            if s == self.target:
                continue
            rect = s.hitbox.copy()
            rect.x += s.get_rect().x
            rect.y += s.get_rect().y
            if rect.intersects(new):
                return True
        return False

    def collide_top(self, dy):
        self.dy = 0

    def collide_bottom(self, dy):
        self.dy = 0

    def collide_left(self, dx):
        self.dx = 0

    def collide_right(self, dx):
        self.dx = 0

def stop_sprite(sprite):
    if sprite.direction == DIR_NORTH and sprite.image != stand_north:
        sprite.image = stand_north
    elif sprite.direction == DIR_SOUTH and sprite.image != stand_south:
        sprite.image = stand_south
    elif sprite.direction == DIR_EAST and sprite.image != stand_east:
        sprite.image = stand_east
    elif sprite.direction == DIR_WEST and sprite.image != stand_west:
        sprite.image = stand_west

def create_sprite(x, y):
    sprite = cocos.sprite.Sprite(stand_south)
    sprite.direction = DIR_SOUTH
    sprite.position = (x, y)
    sprite.hitbox = rect.Rect(4, 0, 30, 38)
    sprite.speed = 300
    sprites.append(sprite)
    return sprite

if __name__ == "__main__":
    from cocos.director import director
    director.init(width=640, height=480, do_not_scale=True, resizable=True)

    sprites = []

    DIR_NORTH = 0
    DIR_SOUTH = 1
    DIR_EAST = 2
    DIR_WEST = 3

    # Load animation
    image = pyglet.resource.image('king.png')
    grid = pyglet.image.ImageGrid(image, 4, 4)
    sequence = grid.get_texture_sequence()
    walk_north = pyglet.image.Animation.from_image_sequence(sequence[:4], .25, loop=True)
    walk_east = pyglet.image.Animation.from_image_sequence(sequence[4:8], .25, loop=True)
    walk_west = pyglet.image.Animation.from_image_sequence(sequence[8:12], .25, loop=True)
    walk_south = pyglet.image.Animation.from_image_sequence(sequence[12:16], .25, loop=True)
    stand_north = pyglet.image.Animation.from_image_sequence(sequence[0:1], .25, loop=True)
    stand_east = pyglet.image.Animation.from_image_sequence(sequence[4:5], .25, loop=True)
    stand_west = pyglet.image.Animation.from_image_sequence(sequence[8:9], .25, loop=True)
    stand_south = pyglet.image.Animation.from_image_sequence(sequence[12:13], .25, loop=True)

    # Load a map and put it in a scrolling layer
    # Setup player sprite
    player_layer = layer.ScrollableLayer()
    player = create_sprite(200, 100)
    player_layer.add(player, z=-player.y)

    action = player.do(MovePlayer())

    # Load a map and put it in a scrolling layer
    scroller = layer.ScrollingManager()
    test_layer = tiles.load('test2-map.xml')['test']
    scroller.add(test_layer)
    scroller.add(player_layer)

    dialog_layer = layer.ColorLayer(64, 69, 83, 255, height=100)

    # Create the main scene
    main_scene = cocos.scene.Scene(scroller)

    # Handle input
    keyboard = key.KeyStateHandler()
    director.window.push_handlers(keyboard)

    state = "walkaround"

    def on_key_press(key, modifier):
        global state # is bad
        global action # is needed
        if state == "walkaround":
            # Zoom in/out
            if key == pyglet.window.key.Z:
                if scroller.scale == .75:
                    scroller.do(actions.ScaleTo(1, 2))
                else:
                    scroller.do(actions.ScaleTo(.75, 2))
            if key == pyglet.window.key.SPACE:
                npc = None
                player_rect = player.hitbox.copy()
                player_rect.x += player.get_rect().x
                player_rect.y += player.get_rect().y
                if player.direction == DIR_NORTH:
                    player_rect.y += player.hitbox.height
                elif player.direction == DIR_SOUTH:
                    player_rect.y -= player.hitbox.height
                elif player.direction == DIR_EAST:
                    player_rect.x += player.hitbox.width
                elif player.direction == DIR_WEST:
                    player_rect.x -= player.hitbox.width
                for s in player_layer.get_children():
                    if s != player:
                        rect = s.hitbox.copy()
                        rect.x += s.get_rect().x
                        rect.y += s.get_rect().y
                        if rect.intersects(player_rect):
                            npc = s
                            break
                if npc != None:
                    state = "dialog"
                    player.remove_action(action)
                    stop_sprite(player)
                    if player.direction == DIR_NORTH:
                        npc.direction = DIR_SOUTH
                        npc.image = stand_south
                    elif player.direction == DIR_SOUTH:
                        npc.direction = DIR_NORTH
                        npc.image = stand_north
                    elif player.direction == DIR_EAST:
                        npc.direction = DIR_WEST
                        npc.image = stand_west
                    elif player.direction == DIR_WEST:
                        npc.direction = DIR_EAST
                        npc.image = stand_east
                    label = cocos.text.Label('Hello! I am an NPC! I wish I had something more interesting to say! Okay, bye!', font_name='DroidSans', font_size=16, multiline=True, width=dialog_layer.width)
                    label.position =(dialog_layer.width/2, dialog_layer.height/2) 
                    label.element.anchor_x = 'center'
                    label.element.anchor_y = 'center'
                    dialog_layer.add(label, name='label')
                    main_scene.add(dialog_layer, z=1)

        elif state == "dialog":
            if key == pyglet.window.key.SPACE:
                state = "walkaround"
                action = player.do(MovePlayer())
                main_scene.remove(dialog_layer)
                dialog_layer.remove('label')

    def on_mouse_press (x, y, buttons, modifiers):
        if state == "walkaround":
            # Add a sprite to screen at the mouse location on right click
            if buttons & mouse.RIGHT:
                new_sprite = create_sprite(*scroller.pixel_from_screen(x, y))
                player_layer.add(new_sprite, z=-new_sprite.y)
            # Left click changes sprite that player is controlling
            elif buttons & mouse.LEFT:
                global player, action
                for s in sprites:
                    if s.get_rect().contains(*scroller.pixel_from_screen(x, y)):
                        player.remove_action(action)
                        player = s
                        action = player.do(MovePlayer())
                        break

    director.window.push_handlers(on_key_press, on_mouse_press)

    # Run game
    director.run(main_scene)

