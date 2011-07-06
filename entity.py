import pyglet
from pyglet.event import EventDispatcher
import cocos
from cocos.cocosnode import CocosNode
from cocos.director import director
import loadmap

class MapActor(cocos.cocosnode.CocosNode):
    def __init__(self, id):
        super(MapActor, self).__init__()
        self.id = id
        self.width = 0
        self.height = 0

    @property
    def size(self):
        return (self.width, self.height)

    @size.setter
    def size(self, size):
        self.width, self.height = size

    def get_rect(self):
        return cocos.rect.Rect(self.x, self.y, self.width, self.height)

class Component(pyglet.event.EventDispatcher):
    def __init__(self):
        super(Component, self).__init__()
        self.parent = None

    def attach(self, parent):
        self.parent = parent

class DialogComponent(object):
    def __init__(self, text):
        self.text = text

class Sign(MapActor):
    def __init__(self, id, dialog):
        super(Sign, self).__init__(id)
        self.dialog = dialog
@loadmap.Map.register_object_factory('sign')
def load_sign(map, name, x, y, width, height, properties):
    text = properties['text']
    sign = Sign(name, DialogComponent(text))
    sign.position = (x, y)
    sign.size = (width, height)
    return sign

class TriggerComponent(EventDispatcher):
    def __init__(self):
        self.trigger_list = None

    def check_triggers(self):
        pass
TriggerComponent.register_event_type('on_actor_enter')
TriggerComponent.register_event_type('on_actor_exit')

class Trigger(MapActor):
    def __init__(self, id, on_actor_enter, on_actor_exit):
        super(Trigger, self).__init__(id)
        self.trigger = TriggerComponent()
        if on_actor_enter != None:
            self.trigger.set_handler(on_actor_enter)
        if on_actor_exit != None:
            self.trigger.set_handler(on_actor_exit)

    def on_enter(self):
        super(Trigger, self).on_enter()
        self.trigger_list = self.parent.triggers

class Portal(MapActor):
    def __init__(self, id, map_file, exit_id):
        super(Portal, self).__init__(id)
        self.map_file = map_file
        self.exit_id = exit_id
        self.trigger = TriggerComponent()
        self.trigger.push_handlers(self.on_actor_enter)
    
    def on_actor_enter(self, actor):
        # Only the player can use portals
        if actor == self.parent.player:
            map = loadmap.load(self.map_file, None)
            map['objects'].add_object(actor)
            map.player = actor
            actor.position = map.find_actor(self.exit_id).position
            director.replace(map)
@loadmap.Map.register_object_factory('portal')
def load_portal(map, name, x, y, width, height, properties):
    map_file = properties['map']
    exit_id = properties['exit']
    portal = Portal(name, map_file, exit_id)
    portal.position = (x, y)
    portal.size = (width, height)
    return portal

class CollisionComponent(EventDispatcher):
    def __init__(self, parent, collidable=True):
        self.parent = parent
        self.collidable = collidable
        self.collision_list = None

    def check_collision(self, x, y):
        # Ignore collision test if collidable flag is not set
        if not self.collidable:
            return False
        # Collision test
        rect = cocos.rect.Rect(x, y, self.parent.width, self.parent.height)
        if self.collision_list == None:
            return False
        for c in self.collision_list:
            if self != c and self.parent.get_rect().intersects(c.parent.get_rect()):
                # Dispatch collision events
                self.dispatch_event('on_collision', c.parent)
                c.dispatch_event('on_collision', self.parent)
                return True
        return False
CollisionComponent.register_event_type('on_collision')

class MoveComponent(EventDispatcher, cocos.actions.Move):
    def init(self, speed, direction='south'):
        self._walking = False
        self._direction = direction
        self.speed = speed

    @property
    def walking(self):
        return self._walking

    @walking.setter
    def walking(self, walking):
        if self._walking == walking:
            return
        self._walking = walking
        self.update_velocity()
        if self._walking:
            self.dispatch_event('on_walk')
        else:
            self.dispatch_event('on_stop')

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        if self._direction == direction:
            return
        self._direction = direction
        self.update_velocity()
        self.dispatch_event('on_change_direction', direction)

    def update_velocity(self):
        if self.walking:
            vx, vy = self.get_direction_vector()
            self.target.velocity = (vx * self.speed, vy * self.speed)
        else:
            self.cancel_movement()

    def get_direction_vector(self):
        if self.direction == 'north':
            return (0, 1)
        elif self.direction == 'south':
            return (0, -1)
        elif self.direction == 'east':
            return (1, 0)
        elif self.direction == 'west':
            return (-1, 0)

    def cancel_movement(self):
        self.target.velocity = (0, 0)

    def start(self):
        super(MoveComponent, self).start()
        self.cancel_movement()

    def step(self, dt):
        vx, vy = self.target.velocity
        self.dispatch_event('on_request_move', vx * dt, vy * dt)
        super(MoveComponent, self).step(dt)
MoveComponent.register_event_type('on_walk')
MoveComponent.register_event_type('on_stop')
MoveComponent.register_event_type('on_change_direction')
MoveComponent.register_event_type('on_request_move')
MoveComponent.register_event_type('on_move')

class InteractComponent(EventDispatcher):
    def __init__(self, parent, span, reach):
        self.parent = parent
        self.span = span
        self.reach = reach

    def interact(self, direction):
        pass
InteractComponent.register_event_type('on_interact')

class Character(MapActor):
    def __init__(self, id, anims, sprite_offset, move):
        super(Character, self).__init__(id)
        self.anims = anims
        self.sprite = cocos.sprite.Sprite(anims['stand_south'])
        self.sprite.image_anchor = (0, 0)
        self.sprite.position = sprite_offset
        self.add(self.sprite)
        self.action = self.do(move)
        self.move = self.actions[self.actions.index(self.action)]
        self.move.push_handlers(self)
        self.collision = CollisionComponent(self)

    def on_walk(self):
        self.sprite.image = self.anims['walk_' + self.move.direction]

    def on_stop(self):
        self.sprite.image = self.anims['stand_' + self.move.direction]

    def on_change_direction(self, direction):
        prefix = 'walk_' if self.move.walking else 'stand_'
        self.sprite.image = self.anims[prefix + self.move.direction]

    def on_request_move(self, dx, dy):
        if self.collision.check_collision(self.x + dx, self.y + dy):
            self.move.cancel_movement()

    def on_move(self, x, y):
        pass

class ObjectLayer(cocos.layer.ScrollableLayer):
    def __init__(self, id=''):
        super(ObjectLayer, self).__init__()
        self.id = id
        self.objects = []

    def add_object(self, obj):
        self.objects.append(obj)
        self.add(obj)
        # If the object is a sprite then add it to the batch for drawing
        #if isinstance(obj, cocos.sprite.Sprite):
        #    self.add(obj, z=-obj.y)
    
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

