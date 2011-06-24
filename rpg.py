# This code is so you can run the samples without installing the package
import sqlite3

import pyglet
from pyglet.window import key, mouse
from pyglet.gl import *

pyglet.resource.path.append(pyglet.resource.get_script_home())
pyglet.resource.reindex()

import cocos
from cocos import tiles, actions, layer, rect

import loadmap
from entity import *

class MovePlayer(actions.Move):
    def step(self, dt):
        global ground_layer
        # Potential velocity if no collision occurs
        self.dx, self.dy = (keyboard[key.RIGHT] - keyboard[key.LEFT]) * self.target.speed, (keyboard[key.UP] - keyboard[key.DOWN]) * self.target.speed

        # Skip collision checks if the sprite isn't moving
        if self.dx != 0 or self.dy != 0:
            self.target.walking = True
            if self.dy > 0:
                self.target.direction = 'north'
            elif self.dy < 0:
                self.target.direction = 'south'
            elif self.dx > 0:
                self.target.direction = 'east'
            elif self.dx < 0:
                self.target.direction = 'west'
            # Create rect for collision testing by translating hitbox by sprite location
            last = self.target.get_hitbox()
            # Test for collision along x axis
            new = last.copy()
            new.x += self.dx * dt
            if self.collide_player(new) or self.check_collision(new):
                self.dx = 0
            # Test for collision along y axis
            new = last.copy()
            new.y += self.dy * dt
            if self.collide_player(new) or self.check_collision(new):
                self.dy = 0
        else:
            self.target.walking = False

        # Set new velocity
        self.target.velocity = (self.dx, self.dy)
        # Get objects that sprite is currently over before moving
        old_objects = map['objects'].get_in_region(self.target.get_hitbox())
        # Move
        super(MovePlayer, self).step(dt)
        # Get objects that sprite is currently over after moving
        new_objects = map['objects'].get_in_region(self.target.get_hitbox())
        # Call on_object_enter event handler for any object that is in the new list but not in the old list
        for obj in new_objects:
            if obj not in old_objects:
                obj.on_object_enter(self.target)
        # Call on_object_exit event handler for any object that is in the old list but not in the new list
        for obj in old_objects:
            if obj not in new_objects:
                    obj.on_object_exit(self.target)
        # Focus scrolling layer on player
        map.set_focus(self.target.x, self.target.y)
        # Y sort
        map['objects'].remove_object(self.target)
        map['objects'].add_object(self.target)

    def check_collision(self, rect):
        for cell in map['collision'].get_in_region(*(rect.bottomleft + rect.topright)):
            if cell.tile != None:
                return True
        return False

    def collide_player(self, new):
        for s in map['objects'].get_in_region(new):
            if s == self.target:
                continue
            if s.collidable and s.get_hitbox().intersects(new):
                return True
        return False

def create_sprite(x, y):
    return Character('King', anims, rect.Rect(x, y, 24, 30), (0, 0), 300)

if __name__ == "__main__":
    from cocos.director import director
    director.init(width=640, height=480, do_not_scale=True, resizable=True)
    director.show_FPS = True

	# Open database
    db = sqlite3.connect('database')
    # Load map
    map = loadmap.Map('outside.tmx', db)

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
    anims = {'stand_north':stand_north, 'stand_south':stand_south, 'stand_east':stand_east, 'stand_west':stand_west, 'walk_north':walk_north, 'walk_south':walk_south, 'walk_east':walk_east, 'walk_west':walk_west}

    # Setup player sprite
    player = create_sprite(450, 200)
    action = player.do(MovePlayer())

    # Add objects to map
    map['objects'].add_object(player)

    dialog_layer = layer.ColorLayer(64, 128, 200,255, height=140)

    # Create the main scene
    main_scene = cocos.scene.Scene(map)

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
                if map.scale == .75:
                    map.do(actions.ScaleTo(1, 2))
                else:
                    map.do(actions.ScaleTo(.75, 2))
            if key == pyglet.window.key.SPACE:
                dialog = None
                player_rect = cocos.rect.Rect(player.x, player.y, 32, 32)#player.get_hitbox()
                if player.direction == 'north':
                    player_rect.y += player_rect.height
                elif player.direction == 'south':
                    player_rect.y -= player_rect.height
                elif player.direction == 'east':
                    player_rect.x += player_rect.width
                elif player.direction == 'west':
                    player_rect.x -= player_rect.width
                for s in map['objects'].get_objects():
                    if s != player and isinstance(s, Dialog):
                        rect = s.get_hitbox()
                        if rect.intersects(player_rect) :
                            dialog = s
                            break
                if dialog != None:
                    dialog.on_interact(player)
                    state = "dialog"
                    player.remove_action(action)
                    player.walking = False
                    label = cocos.text.Label(dialog.text, font_name='DroidSans', font_size=18, multiline=True, width=dialog_layer.width)
                    label.position =(0, dialog_layer.height) 
                    label.element.anchor_y = 'top'
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
                new_sprite = create_sprite(*map.pixel_from_screen(x, y))
                map['objects'].add_object(new_sprite)
            # Left click changes sprite that player is controlling
            elif buttons & mouse.LEFT:
                global player, action
                for s in map['objects'].get_objects():
                    if isinstance(s, Character) and s.get_rect().contains(*map.pixel_from_screen(x, y)):
                        player.remove_action(action)
                        player = s
                        action = player.do(MovePlayer())
                        break

    director.window.push_handlers(on_key_press, on_mouse_press)

    # Run game
    director.run(main_scene)

