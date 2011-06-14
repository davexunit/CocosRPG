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
        global test_layer
        # Potential velocity if no collision occurs
        self.dx, self.dy = (keyboard[key.D] - keyboard[key.A]) * self.target.speed, (keyboard[key.W] - keyboard[key.S]) * self.target.speed

        # Skip collision checks if the sprite isn't moving
        if self.dx != 0 or self.dy != 0:
            self.target.walking = True
            if self.dy > 0:
                self.target.direction = Character.DIR_NORTH
            elif self.dy < 0:
                self.target.direction = Character.DIR_SOUTH
            elif self.dx > 0:
                self.target.direction = Character.DIR_EAST
            elif self.dx < 0:
                self.target.direction = Character.DIR_WEST
            # Create rect for collision testing by translating hitbox by sprite location
            last = self.target.get_hitbox()

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

        # Get cells that sprite is currently over before moving
        target_x, target_y = self.target.get_rect().x + self.target.hitbox.x, self.target.get_rect().y + self.target.hitbox.y, 
        old_cells = test_layer.get_in_region(target_x, target_y, target_x + self.target.hitbox.width, target_y + self.target.hitbox.height)

        # Move
        super(MovePlayer, self).step(dt)

        # Get cells that sprite is currently over after moving
        target_x, target_y = self.target.get_rect().x + self.target.hitbox.x, self.target.get_rect().y + self.target.hitbox.y, 
        new_cells = test_layer.get_in_region(target_x, target_y, target_x + self.target.hitbox.width, target_y + self.target.hitbox.height)

        # For any cells in the new list that are not in the old list, analyze their properties and act accordingly
        for cell in new_cells:
            if cell not in old_cells:
                if cell.get('portal'):
                    # Arguments are separated by a colon
                    map_file, map = cell.get('portal').split(':')
                    # Remove map
                    scroller.remove(test_layer)
                    # Load new map
                    test_layer = tiles.load(map_file)[map]
                    # Add new map
                    scroller.add(test_layer)

        # Focus scrolling layer on player
        scroller.set_focus(self.target.x, self.target.y)
        # Y sort
        object_layer.remove_object(self.target)
        object_layer.add_object(self.target)

    def collide_player(self, new):
        for s in object_layer.get_objects():
            if s == self.target:
                continue
            if s.collidable and s.get_hitbox().intersects(new):
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

class MapObject(object):
    def __init__(self, id, hitbox, collidable=True):
        self.id = id
        self.hitbox= hitbox.copy()
        self.collidable = collidable

    def get_hitbox(self):
        return self.hitbox.copy()

class Portal(MapObject):
    def __init__(self, id, rect, map_file, collidable=False):
        super(Portal, self).__init__(id, rect, collidable)
        self.map_file = map_file

class Character(MapObject, cocos.sprite.Sprite):
    DIR_NORTH = 0
    DIR_SOUTH = 1
    DIR_EAST = 2
    DIR_WEST = 3

    def __init__(self, id, anims, hitbox, speed, direction=DIR_SOUTH, collidable=True):
        '''Anims is a list of pyglet.image.Animation.
        Order:
            standing north, standing south, standing east, standing west, walking north, walking south, walking east, walking west
        '''
        self.speed = speed
        self._direction = direction
        self._walking = False
        self.anims = anims
        cocos.sprite.Sprite.__init__(self, self.anims[self._direction])
        MapObject.__init__(self, id, hitbox, collidable)

    def get_hitbox(self):
        rect = self.hitbox.copy()
        rect.x += self.get_rect().x
        rect.y += self.get_rect().y
        return rect

    def _update_animation(self):
        offset = 4 if self._walking else 0
        if self._direction == self.DIR_NORTH:
            self.image = self.anims[offset]
        elif self._direction == self.DIR_SOUTH:
            self.image = self.anims[offset + 1]
        elif self._direction == self.DIR_EAST:
            self.image = self.anims[offset + 2]
        elif self._direction == self.DIR_WEST:
            self.image = self.anims[offset + 3]

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, dir):
        if self._direction != dir:
            self._direction = dir
            self._update_animation()

    @property
    def walking(self):
        return self._walking

    @walking.setter
    def walking(self, walking):
        if self._walking != walking:
            self._walking = walking
            self._update_animation()

class ObjectLayer(cocos.layer.ScrollableLayer):
    def __init__(self, id=''):
        super(ObjectLayer, self).__init__()
        self.id = id
        self.objects = []
        self.batch = cocos.batch.BatchNode()
        self.add(self.batch)

    def add_object(self, obj):
        self.objects.append(obj)
        # If the object is a sprite then add it to the batch for drawing
        if isinstance(obj, cocos.sprite.Sprite):
            self.batch.add(obj, z=obj.y)
    
    def remove_object(self, obj):
        self.objects.remove(obj)
        # If the object is a sprite then remove it from the batch
        if isinstance(obj, cocos.sprite.Sprite):
            self.batch.remove(obj)

    def get_objects(self):
        return self.objects

@cocos.tiles.Resource.register_factory('objects')
def objectlayer_factory(resource, tag):
    obj_layer = ObjectLayer()
    for child in tag:
        # Construct bounding box
        x, y = child.get('xy').split(',')
        x, y = int(x), int(y)
        w, h = child.get('wh').split(',')
        w, h = int(w), int(h)
        hitbox = cocos.rect.Rect(x, y, w, h)
        # Get object identifier
        id = child.get('id')
        # Get collidable
        collidable = child.get('collidable')
        obj = None
        # Object factory
        if child.tag == 'portal':
            obj = _handle_portal(child, id, hitbox, collidable)
        if obj != None:
            obj_layer.add_object(obj)

    if tag.get('id'):
        obj_layer.id = tag.get('id')
        resource.add_resource(obj_layer.id, obj_layer)

    return obj_layer

def _handle_portal(tag, hitbox, id, collidable):
    if collidable == None:
        collidable = False
    map_file = tag.get('map')
    return Portal(rect, id, map_file, collidable)

def stop_sprite(sprite):
    sprite.walking = False

def create_sprite(x, y):
    sprite = Character('King', anims, rect.Rect(4, 0, 30, 38), 300)
    sprite.position = (x, y)
    return sprite

if __name__ == "__main__":
    from cocos.director import director
    director.init(width=640, height=480, do_not_scale=True, resizable=True)

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
    anims = [stand_north, stand_south, stand_east, stand_west, walk_north, walk_south, walk_east, walk_west]

    # Setup player sprite
    #object_layer = layer.ScrollableLayer()
    player = create_sprite(200, 100)
    #object_layer.add_object(player, z=-player.y)

    action = player.do(MovePlayer())

    # Load map
    map = tiles.load('test2-map.xml')

    # Load a map and put it in a scrolling layer
    scroller = layer.ScrollingManager()
    test_layer = map['ground']
    scroller.add(test_layer)
    #scroller.add(object_layer)

    # Load object layer and add it to the scrolling layer
    object_layer = map['objects']
    object_layer.add_object(player)
    scroller.add(object_layer, z=1)

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
                player_rect = player.get_hitbox()
                if player.direction == Character.DIR_NORTH:
                    player_rect.y += player.hitbox.height
                elif player.direction == Character.DIR_SOUTH:
                    player_rect.y -= player.hitbox.height
                elif player.direction == Character.DIR_EAST:
                    player_rect.x += player.hitbox.width
                elif player.direction == Character.DIR_WEST:
                    player_rect.x -= player.hitbox.width
                for s in object_layer.get_objects():
                    if s != player:
                        rect = s.get_hitbox()
                        if rect.intersects(player_rect):
                            npc = s
                            break
                if npc != None:
                    state = "dialog"
                    player.remove_action(action)
                    stop_sprite(player)
                    if player.direction == Character.DIR_NORTH:
                        npc.direction = Character.DIR_SOUTH
                    elif player.direction == Character.DIR_SOUTH:
                        npc.direction = Character.DIR_NORTH
                    elif player.direction == Character.DIR_EAST:
                        npc.direction = Character.DIR_WEST
                    elif player.direction == Character.DIR_WEST:
                        npc.direction = Character.DIR_EAST
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
                object_layer.add_object(new_sprite)
            # Left click changes sprite that player is controlling
            elif buttons & mouse.LEFT:
                global player, action
                for s in object_layer.get_objects():
                    if isinstance(s, Character) and s.get_rect().contains(*scroller.pixel_from_screen(x, y)):
                        player.remove_action(action)
                        player = s
                        action = player.do(MovePlayer())
                        break

    director.window.push_handlers(on_key_press, on_mouse_press)

    # Run game
    director.run(main_scene)

