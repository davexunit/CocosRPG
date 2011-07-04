import cocos
import loadmap

class MapEntity(object):
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

    def on_interact(self, player):
        '''Event called when player character interacts with this object
        '''
        pass

class Trigger(MapEntity):
    def __init__(self, id, rect, enter_func, exit_func, collidable=False):
        super(Trigger, self).__init__(id, rect, collidable)
        self.enter_func = enter_func
        self.exit_func = exit_func

    def on_object_enter(self, obj):
        if self.enter_func != None:
            self.enter_func(obj)

    def on_object_exit(self, obj):
        if self.exit_func != None:
            self.exit_func(obj)

class Dialog(MapEntity):
    def __init__(self, id, rect, text, collidable=False):
        super(Dialog, self).__init__(id, rect, collidable)
        self.text = text
@loadmap.Map.register_object_factory('dialog')
def load_dialog(map, name, rect, properties):
    text = properties['text']
    return Dialog(name, rect, text)

class Portal(MapEntity):
    def __init__(self, id, rect, map, map_file, spawn_position, collidable=False):
        super(Portal, self).__init__(id, rect, collidable)
        self.map_file = map_file
        self.map = map
        self.spawn_position = spawn_position
    
    def on_object_enter(self, obj):
        self.map.load(self.map_file)
        self.map['objects'].add_object(obj)
        obj.position = self.spawn_position

    def on_object_exit(self, obj):
        pass
@loadmap.Map.register_object_factory('portal')
def load_portal(map, name, rect, properties):
    map_file = properties['map']
    spawn = tuple([int(x) for x in properties['spawn'].split(',')])
    return Portal(name, rect, map, map_file, spawn)

class Character(Dialog, cocos.sprite.Sprite):
    def __init__(self, id, anims, hitbox, offset, speed, direction='south', collidable=True, dialog=None):
        '''Anims is a list of pyglet.image.Animation.
        Order:
            standing north, standing south, standing east, standing west, walking north, walking south, walking east, walking west
        '''
        self.speed = speed
        self._direction = direction
        self._walking = False
        self.anims = anims
        if dialog == None:
            dialog = 'Hello. My name is %s' % id
        Dialog.__init__(self, id, hitbox, dialog, collidable)
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

    def on_interact(self, player):
        if player.direction == 'north':
            self.direction = 'south'
        elif player.direction == 'south':
            self.direction = 'north'
        elif player.direction == 'east':
            self.direction = 'west'
        elif player.direction == 'west':
            self.direction = 'east'

class ObjectLayer(cocos.layer.ScrollableLayer):
    def __init__(self, id=''):
        super(ObjectLayer, self).__init__()
        self.id = id
        self.objects = []

    def add_object(self, obj):
        self.objects.append(obj)
        # If the object is a sprite then add it to the batch for drawing
        if isinstance(obj, cocos.sprite.Sprite):
            self.add(obj, z=-obj.y)
    
    def remove_object(self, obj):
        self.objects.remove(obj)
        # If the object is a sprite then remove it from the batch
        if isinstance(obj, cocos.sprite.Sprite):
            self.remove(obj)

    def get_objects(self):
        return self.objects

    def get_in_region(self, rect):
        objs = []
        for o in self.objects:
            if o.get_hitbox().intersects(rect):
                objs.append(o)
        return objs

