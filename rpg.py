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

class MapController(object):
    def on_start(self):
        pass

    def on_stop(self):
        pass

def create_sprite(x, y):
    return Character('King', anims, rect.Rect(x, y, 24, 30), (0, 0), 300)

def make_dialog_box():
    image = pyglet.resource.image('Dialog_Border.png')
    grid = pyglet.image.ImageGrid(image, 3, 3)
    w = cocos.director.director.get_window_size()[0]
    num_columns, num_rows = w / grid.item_width, 128 / grid.item_height
    columns = list()
    for i in range(0, num_columns):
        row = list()
        columns.append(row)
        for j in range(0, num_rows):
            if i == 0 and j == 0:
                index = 0
            elif i == 0 and j == num_rows - 1:
                index = 6
            elif i == num_columns - 1 and j == 0:
                index = 2
            elif i == num_columns - 1 and j == num_rows - 1:
                index = 8
            elif i == 0 and j != 0 and j != num_rows - 1:
                index = 3
            elif i == num_columns - 1 and j != 0 and j != num_rows - 1:
                index = 5
            elif i != 0 and i != num_columns - 1  and j == 0:
                index = 1
            elif i != 0 and i != num_columns - 1  and j == num_rows - 1:
                index = 7
            else:
                index = 4
            tile = cocos.tiles.Tile(1, None, grid[index])
            row.append(cocos.tiles.RectCell(i, j, grid.item_width, grid.item_height, None, tile))
    dialog_box = cocos.tiles.RectMapLayer('Dialog', grid.item_width, grid.item_height, columns, (0,0,0), None)
    dialog_box.set_view(0, 0, dialog_box.px_width, dialog_box.px_height)
    return dialog_box

if __name__ == "__main__":
    from cocos.director import director
    director.init(width=640, height=480, do_not_scale=True, resizable=True)
    director.show_FPS = True

	# Open database
    db = sqlite3.connect('database')
    # Load map
    map = loadmap.Map('outside.tmx', db)
    # Load animation
    anims = loadmap.load_animset('king.xml')
    # Setup player sprite
    player = create_sprite(450, 200)
    action = player.do(MovePlayer())
    # Add objects to map
    map['objects'].add_object(player)
    dialog_layer = make_dialog_box()
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
                    label = cocos.text.Label(dialog.text, font_name='DroidSans', font_size=18, multiline=True, width=dialog_layer.px_width)
                    label.position = (32, dialog_layer.px_height - 32) 
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

