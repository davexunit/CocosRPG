# This code is so you can run the samples without installing the package
import pyglet
from pyglet.window import key, mouse
from pyglet.gl import *

pyglet.resource.path.append(pyglet.resource.get_script_home())
pyglet.resource.reindex()

import cocos
from cocos import tiles, actions, layer, rect

class MovePlayer(actions.Move, tiles.RectMapCollider):
    def step(self, dt):
        global ground_layer
        # Potential velocity if no collision occurs
        self.dx, self.dy = (keyboard[key.D] - keyboard[key.A]) * self.target.speed, (keyboard[key.W] - keyboard[key.S]) * self.target.speed

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
            if self.collide_player(new):
                self.dx = 0
            else:
                self.collide_map(ground_layer, last, new, None, None)
                self.collide_map(fringe_layer, last, new, None, None)

            # Test for collision along y axis
            new = last.copy()
            new.y += self.dy * dt
            if self.collide_player(new):
                self.dy = 0
            else:
                self.collide_map(ground_layer, last, new, None, None)
                self.collide_map(fringe_layer, last, new, None, None)
        else:
            stop_sprite(self.target)

        # Set new velocity
        self.target.velocity = (self.dx, self.dy)

        # Get objects that sprite is currently over before moving
        old_objects = object_layer.get_in_region(self.target.get_hitbox())

        # Move
        super(MovePlayer, self).step(dt)

        # Get objects that sprite is currently over after moving
        new_objects = object_layer.get_in_region(self.target.get_hitbox())

        # Call on_object_enter event handler for any object that is in the new list but not in the old list
        for obj in new_objects:
            if obj not in old_objects:
                obj.on_object_enter(self.target)
        # Call on_object_exit event handler for any object that is in the old list but not in the new list
        for obj in old_objects:
            if obj not in new_objects:
                    obj.on_object_exit(self.target)

        # Focus scrolling layer on player
        scroller.set_focus(self.target.x, self.target.y)
        # Y sort
        object_layer.remove_object(self.target)
        object_layer.add_object(self.target)

    def collide_player(self, new):
        for s in object_layer.get_in_region(new):
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

    def on_object_enter(self, obj):
        pass

    def on_object_exit(self, obj):
        pass

class Portal(MapObject):
    def __init__(self, id, rect, map_file, collidable=False):
        super(Portal, self).__init__(id, rect, collidable)
        self.map_file = map_file
    
    def on_object_enter(self, obj):
        global ground_layer, object_layer, map
        print obj.id, "in", self.map_file
        scroller.remove(ground_layer)
        scroller.remove(object_layer)
        map = tiles.load(self.map_file)
        ground_layer = map['ground']
        object_layer = map['objects']
        object_layer.add_object(obj)
        scroller.add(ground_layer)
        scroller.add(object_layer, z=1)

    def on_object_exit(self, obj):
        print obj.id, "out"

class Dialog(MapObject):
    def __init__(self, id, rect, text, collidable=False):
        super(Dialog, self).__init__(id, rect, collidable)
        self.text = text

class Character(MapObject, cocos.sprite.Sprite):
    def __init__(self, id, anims, hitbox, offset, speed, direction='south', collidable=True):
        '''Anims is a list of pyglet.image.Animation.
        Order:
            standing north, standing south, standing east, standing west, walking north, walking south, walking east, walking west
        '''
        self.speed = speed
        self._direction = direction
        self._walking = False
        self.anims = anims
        MapObject.__init__(self, id, hitbox, collidable)
        cocos.sprite.Sprite.__init__(self, self.anims['stand_' + self._direction])
        super(Character, self)._set_position(hitbox.position)
        self.image_anchor = (0, 0)

    def _update_animation(self):
        prefix = 'walk_' if self._walking else 'stand_'
        self.image = self.anims[prefix + self._direction]

    def _set_x(self, x):
        super(Character, self)._set_x(x)
        self.hitbox.x = x

    def _set_y(self, y):
        super(Character, self)._set_y(y)
        self.hitbox.y = y

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

    def get_in_region(self, rect):
        objs = []
        for o in self.objects:
            if o.get_hitbox().intersects(rect):
                objs.append(o)
        return objs

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
        elif child.tag == 'dialog':
            obj = _handle_dialog(child, id, hitbox, collidable)
        elif child.tag == 'character':
            obj = _handle_character(child, id, hitbox, collidable)
        if obj != None:
            obj_layer.add_object(obj)

    if tag.get('id'):
        obj_layer.id = tag.get('id')
        resource.add_resource(obj_layer.id, obj_layer)

    return obj_layer

def _handle_character(tag, id, hitbox, collidable):
    if collidable == None:
        collidable = True
    image = pyglet.resource.get(tag.get('image'))
    speed = tag.get('speed')
    direction = tag.get('direction')
    if tag.get('direction') == None:
        direction = 'south'
    anims = _handle_anims(tag.findall('anim'))

def _handle_anims(tags):
    for tag in tags:
        print tag

def _handle_portal(tag, hitbox, id, collidable):
    if collidable == None:
        collidable = False
    map_file = tag.get('map')
    return Portal(rect, id, map_file, collidable)

def _handle_dialog(tag, id, hitbox, collidable):
    if collidable == None:
        collidable = False
    text = tag.get('text')
    return Dialog(id, hitbox, text, collidable)

def stop_sprite(sprite):
    sprite.walking = False

def create_sprite(x, y):
    sprite = Character('King', anims, rect.Rect(x, y, 28, 32), (-4, 0), 500)
    return sprite

class Fountain(MapObject, cocos.sprite.Sprite):
    def __init__(self, id, hitbox, anims, collidable=False):
        MapObject.__init__(self, id, hitbox, collidable)
        cocos.sprite.Sprite.__init__(self, anims['idle'])
        self.anims = anims
        self.position = hitbox.position
        self.image_anchor = (0, 0)
    
    def on_object_enter(self, object):
        self.image = self.anims['active']

    def on_object_exit(self, object):
        self.image = self.anims['idle']

if __name__ == "__main__":
    from cocos.director import director
    director.init(width=640, height=480, do_not_scale=True, resizable=True)
    director.show_FPS = True

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
    image2 = pyglet.resource.image('fountain.png')
    grid2 = pyglet.image.ImageGrid(image2, 4, 3)
    sequence2 = grid2.get_texture_sequence()
    idle = pyglet.image.Animation.from_image_sequence(sequence2[0:3], .1, loop=True)
    active = pyglet.image.Animation.from_image_sequence(sequence2[9:12], .1, loop=True)
    anims2 = {'idle':idle, 'active':active}
    fountain = Fountain('fountain', cocos.rect.Rect(256, 256, 32, 32), anims2)

    # Setup player sprite
    player = create_sprite(200, 100)

    action = player.do(MovePlayer())

    # Load map
    map = tiles.load('test4-map.xml')

    # Load a map and put it in a scrolling layer
    scroller = layer.ScrollingManager()
    ground_layer = map['ground']
    fringe_layer = map['fringe']
    over_layer = map['over']
    scroller.add(ground_layer, z=0)
    scroller.add(fringe_layer, z=1)
    scroller.add(over_layer, z=3)

    # Load object layer and add it to the scrolling layer
    object_layer = map['objects'] if 'objects' in map else ObjectLayer()
    object_layer.add_object(player)
    object_layer.add_object(fountain)
    scroller.add(object_layer, z=2)

    dialog_layer = layer.ColorLayer(64, 69, 83, 255, height=90)

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
                dialog = None
                player_rect = player.get_hitbox()
                if player.direction == 'north':
                    player_rect.y += player.hitbox.height
                elif player.direction == 'south':
                    player_rect.y -= player.hitbox.height
                elif player.direction == 'east':
                    player_rect.x += player.hitbox.width
                elif player.direction == 'west':
                    player_rect.x -= player.hitbox.width
                for s in object_layer.get_objects():
                    if s != player and isinstance(s, Dialog):
                        rect = s.get_hitbox()
                        if rect.intersects(player_rect) :
                            dialog = s
                            break
                if dialog != None:
                    state = "dialog"
                    player.remove_action(action)
                    stop_sprite(player)
                    '''
                    if player.direction == 'north':
                        npc.direction = 'south'
                    elif player.direction == 'south':
                        npc.direction = 'north'
                    elif player.direction == 'east':
                        npc.direction = 'west'
                    elif player.direction == 'west':
                        npc.direction = 'east'
                    '''
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

