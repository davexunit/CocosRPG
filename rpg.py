# This code is so you can run the samples without installing the package
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pyglet
from pyglet.window import key
from pyglet.gl import *

pyglet.resource.path.append(pyglet.resource.get_script_home())
pyglet.resource.reindex()

import cocos
from cocos import tiles, actions, layer

class MovePlayer(actions.Move, tiles.RectMapCollider):
    def step(self, dt):
        last = self.target.get_rect()
        new = last.copy()
        self.dx, self.dy = (keyboard[key.RIGHT] - keyboard[key.LEFT]) * self.target.speed, (keyboard[key.UP] - keyboard[key.DOWN]) * self.target.speed
        new.x += self.dx * dt
        new.y += self.dy * dt
        self.collide_map(test_layer, last, new, None, None)
        self.target.velocity = (self.dx, self.dy)
        super(MovePlayer, self).step(dt)
        scroller.set_focus(self.target.x, self.target.y)

    def collide_top(self, dy):
        self.dy = dy

    def collide_bottom(self, dy):
        self.dy = dy

    def collide_left(self, dx):
        self.dx = dx

    def collide_right(self, dx):
        self.dx = dx

if __name__ == "__main__":
    from cocos.director import director
    director.init(width=600, height=300, do_not_scale=True, resizable=True)

    # Setup player sprite
    car_layer = layer.ScrollableLayer()
    car = cocos.sprite.Sprite('car.png')
    car_layer.add(car)
    car.position = (200, 100)
    car.speed = 300
    car.do(MovePlayer())

    # Load a map and put it in a scrolling layer
    scroller = layer.ScrollingManager()
    test_layer = tiles.load('test-map.xml')['map0']
    scroller.add(test_layer)
    scroller.add(car_layer)

    cell = test_layer.get_cell(0, 3)
    print cell.tile.properties.get('bottom')

    # Create the main scene
    main_scene = cocos.scene.Scene(scroller)

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
        # Debug mode on/off
        elif key == pyglet.window.key.D:
            test_layer.set_debug(True)
    director.window.push_handlers(on_key_press)

    # Run game
    director.run(main_scene)

