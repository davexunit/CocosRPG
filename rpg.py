# This code is so you can run the samples without installing the package
import sqlite3
import sys
import utility

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
    def start(self):
        # Handle input
        self.keyboard = key.KeyStateHandler()
        director.window.push_handlers(self.keyboard)

    def step(self, dt):
        # Potential velocity if no collision occurs
        self.dx, self.dy = (self.keyboard[key.RIGHT] - self.keyboard[key.LEFT]) * self.target.speed, (self.keyboard[key.UP] - self.keyboard[key.DOWN]) * self.target.speed

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
        old_objects = map_scene.map_layer['objects'].get_in_region(self.target.get_hitbox())
        # Move
        super(MovePlayer, self).step(dt)
        # Get objects that sprite is currently over after moving
        new_objects = map_scene.map_layer['objects'].get_in_region(self.target.get_hitbox())
        # Call on_object_enter event handler for any object that is in the new list but not in the old list
        for obj in new_objects:
            if obj not in old_objects:
                obj.on_object_enter(self.target)
        # Call on_object_exit event handler for any object that is in the old list but not in the new list
        for obj in old_objects:
            if obj not in new_objects:
                    obj.on_object_exit(self.target)
        # Focus scrolling layer on player
        map_scene.map_layer.set_focus(self.target.x, self.target.y)
        # Y sort
        map_scene.map_layer['objects'].remove_object(self.target)
        map_scene.map_layer['objects'].add_object(self.target)

    def check_collision(self, rect):
        for cell in map_scene.map_layer['collision'].get_in_region(*(rect.bottomleft + rect.topright)):
            if cell.tile != None:
                return True
        return False

    def collide_player(self, new):
        for s in map_scene.map_layer['objects'].get_in_region(new):
            if s == self.target:
                continue
            if s.collidable and s.get_hitbox().intersects(new):
                return True
        return False

class State(cocos.layer.Layer):
    '''State objects control the tile engine.
    State objects register input events and perform their specific task.
    Common tile engines states are: Walkaround, Dialog, and Cinematic
    Each State should perform a unique task.
    '''
    is_event_handler = True

class WalkaroundState(State):
    def on_enter(self):
        super(WalkaroundState, self).on_enter()
        self.action = map_scene.player.do(MovePlayer())

    def on_exit(self):
        super(WalkaroundState, self).on_exit()
        map_scene.player.remove_action(self.action)

    def on_key_press(self, key, modifier):
        if key == pyglet.window.key.SPACE:
			# Entity to possibly interact with
            entity = None
            player = self.parent.player
			# Translate hitbox up, down, left, or right depending on player direction
            player_rect = cocos.rect.Rect(player.x, player.y, 32, 32)#player.get_hitbox()
            if player.direction == 'north':
                player_rect.y += player_rect.height
            elif player.direction == 'south':
                player_rect.y -= player_rect.height
            elif player.direction == 'east':
                player_rect.x += player_rect.width
            elif player.direction == 'west':
                player_rect.x -= player_rect.width
		    # Check for entities with dialog
            for s in self.parent.map_layer['objects'].get_objects():
                if s != player and isinstance(s, Dialog):
                    rect = s.get_hitbox()
                    if rect.intersects(player_rect) :
                        entity = s
                        break
            if entity != None:
                entity.on_interact(player)
                player.walking = False
                self.parent.state_push(DialogState(entity.text))

    def on_mouse_press (self, x, y, buttons, modifiers):
        '''This is just to test some stuff. Should be removed at some point.
        '''
        # Add a sprite to screen at the mouse location on right click
        if buttons & mouse.RIGHT:
            new_sprite = create_sprite('new', *self.parent.map_layer.pixel_from_screen(x, y))
            self.parent.map_layer['objects'].add_object(new_sprite)
        # Left click changes sprite that player is controlling
        elif buttons & mouse.LEFT:
            for s in self.parent.map_layer['objects'].get_objects():
                if isinstance(s, Character) and s.get_rect().contains(*self.parent.map_layer.pixel_from_screen(x, y)):
                    self.parent.player.remove_action(self.action)
                    self.parent.player = s
                    self.action = self.parent.player.do(MovePlayer())
                    break

class DialogState(State):
    def __init__(self, text):
        super(DialogState, self).__init__()
        self.text = text
        self.dialog_layer = self._make_dialog_layer()
        self.label = cocos.text.Label(text, font_name='DroidSans', font_size=16, multiline=True, width=self.dialog_layer.px_width)
        self.label.position = (16, self.dialog_layer.px_height - 16) 
        self.label.element.anchor_y = 'top'
        self.dialog_layer.add(self.label, name='label')
 
    def _make_dialog_layer(self):
        # Load dialog box border
        image = pyglet.resource.image('Dialog_Border.png')
        # The border is a 3x3 tile grid
        grid = pyglet.image.ImageGrid(image, 3, 3)
        # The width of the dialog box will be the width of the window
        w = cocos.director.director.get_window_size()[0]
        # Calculate how many tiles can fit in the space we have to fill
        num_columns, num_rows = w / grid.item_width, 128 / grid.item_height
        # Construct rectmap that creates a dialog box border
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
        dialog_layer = cocos.tiles.RectMapLayer('Dialog', grid.item_width, grid.item_height, columns, (0,0,0), None)
        # Set the view of the dialog box to exactly the size of the dialog box
        dialog_layer.set_view(0, 0, dialog_layer.px_width, dialog_layer.px_height)
        return dialog_layer

    def on_enter(self):
        super(DialogState, self).on_enter()
        self.parent.add(self.dialog_layer, z=1)

    def on_exit(self):
        super(DialogState, self).on_exit()
        self.parent.remove(self.dialog_layer)

    def on_key_press(self, key, modifier):
        if key == pyglet.window.key.SPACE:
            self.parent.state_pop()

class CinematicState(State):
    pass

class TileMapScene(cocos.scene.Scene):
    def __init__(self, map_filename, db_filename):
        super(TileMapScene, self).__init__()
        self.map_filename = map_filename
        self.db_filename = db_filename
        self.db = sqlite3.connect(utility.resource_path(db_filename))
        self.map_layer = loadmap.Map(map_filename, self.db)
        self.state = list()
        self.player = None
        # Add map_layer to scene
        self.add(self.map_layer)

    def state_replace(self, new_state):
        # Remove old state is there was one and suppress the exception
        try:
            self.remove(self.state.pop())
        except IndexError:
            pass
        self.state_push(new_state)

    def state_push(self, new_state):
        # Push new state
        try:
            self.remove(self.state[-1])
        except:
            pass
        self.state.append(new_state)
        self.add(new_state)

    def state_pop(self):
        self.remove(self.state.pop())
        self.add(self.state[-1])

if __name__ == "__main__":
    from cocos.director import director
    director.init(width=640, height=480, do_not_scale=True, resizable=True)
    director.show_FPS = True

    # Add resource file paths
    pyglet.resource.path.append('data')
    pyglet.resource.path.append('data/images')
    pyglet.resource.path.append('data/maps')
    pyglet.resource.path.append('data/anims')
    pyglet.resource.reindex()

    # Load map scene
    map_scene = TileMapScene('outside.tmx', 'database')
    map_scene.state_replace(WalkaroundState())

    def create_sprite(name, x, y):
        return Character(name, anims, rect.Rect(x, y, 24, 30), (0, 0), 300)
    # Load animation
    anims = loadmap.load_animset('king.xml')
    # Setup player sprite
    player = create_sprite('player', 450, 200)
    # Add objects to map
    map_scene.map_layer['objects'].add_object(player)
    map_scene.player = player
    keyboard = key.KeyStateHandler()
    director.window.push_handlers(keyboard)
    director.run(map_scene)
