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
            # Create rect for collision testing by translating hitbox by sprite location
            last = self.target.hitbox.copy()
            last.x += self.target.get_rect().x
            last.y += self.target.get_rect().y

            # Test for collision along x axis
            new = last.copy()
            new.x += self.dx * dt
            self.collide_map(test_layer, last, new, None, None)

            # Test for collision along y axis
            new = last.copy()
            new.y += self.dy * dt
            self.collide_map(test_layer, last, new, None, None)

        # Set new velocity
        self.target.velocity = (self.dx, self.dy)

        # Move
        super(MovePlayer, self).step(dt)

        # Focus scrolling layer on player
        scroller.set_focus(self.target.x, self.target.y)

    def collide_top(self, dy):
        self.dy = 0

    def collide_bottom(self, dy):
        self.dy = 0

    def collide_left(self, dx):
        self.dx = 0

    def collide_right(self, dx):
        self.dx = 0

class SpritePicker(cocos.layer.Layer):
    is_event_handler = True

def create_sprite(x, y):
    sprite = cocos.sprite.Sprite('king_single.png')
    sprite.position = (x, y)
    sprite.hitbox = rect.Rect(4, 0, 30, 38)
    sprite.speed = 300
    sprites.append(sprite)
    return sprite

if __name__ == "__main__":
    from cocos.director import director
    director.init(width=640, height=480, do_not_scale=True, resizable=True)

    sprites = []

    # Load a map and put it in a scrolling layer
    # Setup player sprite
    player_layer = layer.ScrollableLayer()
    player = create_sprite(200, 100)
    player_layer.add(player)

    action = player.do(MovePlayer())

    # Load a map and put it in a scrolling layer
    scroller = layer.ScrollingManager()
    test_layer = tiles.load('test2-map.xml')['test']
    scroller.add(test_layer)
    scroller.add(player_layer)

    # Create the main scene
    main_scene = cocos.scene.Scene(scroller, SpritePicker())

    # Handle input
    keyboard = key.KeyStateHandler()
    director.window.push_handlers(keyboard)

    def on_key_press(key, modifier):
        # Zoom in/out
        if key == pyglet.window.key.Z:
            if scroller.scale == .75:
                scroller.do(actions.ScaleTo(1, 2))
            else:
                scroller.do(actions.ScaleTo(.75, 2))

    def on_mouse_press (x, y, buttons, modifiers):
        # Add a sprite to screen at the mouse location on right click
        if buttons & mouse.RIGHT:
            new_sprite = create_sprite(*scroller.pixel_from_screen(x, y))
            player_layer.add(new_sprite)
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

