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
    def __init__(self, parent, trigger_list):
        self.parent = parent
        self.trigger_list = trigger_list

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
        self.trigger = TriggerComponent(self, None)
        self.trigger.push_handlers(self.on_actor_enter)
    
    def on_actor_enter(self, actor):
        # Only the player can use portals
        if actor == self.parent.player:
            map = loadmap.load(self.map_file, None)
            map['actors'].add_object(actor)
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

    def check_collision(self, x, y):
        pass
CollisionComponent.register_event_type('on_collision')

class ActorCollisionComponent(CollisionComponent):
    def __init__(self, parent, collidable=True):
        super(ActorCollisionComponent, self).__init__(parent, collidable)
        self.collision_list = None

    def check_collision(self, x, y):
        # Ignore collision test if collidable flag is not set
        if not self.collidable:
            return False
        # Check for collision with other collision components
        rect = cocos.rect.Rect(x, y, self.parent.width, self.parent.height)
        for c in self.collision_list:
            if self != c and c.collidable and rect.intersects(c.parent.get_rect()):
                # Dispatch collision events
                self.dispatch_event('on_collision', c.parent)
                c.dispatch_event('on_collision', self.parent)
                return True
        return False

class MapCollisionComponent(CollisionComponent):
    def __init__(self, parent, collidable=True):
        super(MapCollisionComponent, self).__init__(parent, collidable)
        self.collision_map = None

    def check_collision(self, x, y):
        # Ignore collision test if collidable flag is not set
        if not self.collidable:
            return False
        rect = cocos.rect.Rect(x, y, self.parent.width, self.parent.height)
        for cell in self.collision_map.get_in_region(*(rect.bottomleft + rect.topright)):
            if cell.tile != None:
                self.dispatch_event('on_collision', cell)
                return True
        return False

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
            self.target.velocity = (vx * self.speed * 1.0, vy * self.speed * 1.0)
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
        # Request movement (movement can be stopped by event handler)
        vx, vy = self.target.velocity
        if vx != 0 or vy != 0:
            self.dispatch_event('on_request_move', vx * dt, vy * dt)
        super(MoveComponent, self).step(dt)
        self.target.x = int(self.target.x)
        self.target.y = int(self.target.y)
        # If movement hasn't been stopped then dispatch on_move event
        vx, vy = self.target.velocity
        if vx != 0 or vy != 0:
            self.dispatch_event('on_move', self.target.x, self.target.y)
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
        self.interact_list = None

    def interact(self, direction):
        # Create bounding box based on direction that the actor is facing
        rect = self.parent.get_rect()
        if direction == 'north':
            rect.y += rect.height
            rect.height = self.reach
        elif direction == 'south':
            rect.y -= rect.height + self.reach
            rect.height = self.reach
        elif direction == 'east':
            rect.x += rect.width
            rect.width = self.reach
        elif direction == 'west':
            rect.x -= rect.width + self.reach
            rect.width = self.reach
        # Check for rect collisions with other registered interaction components
        for i in self.interact_list:
            pass
InteractComponent.register_event_type('on_interact')

class Character(MapActor):
    def __init__(self, id, anims, sprite_offset, move, collision_map, collision_list):
        super(Character, self).__init__(id)
        self.anims = anims
        # Sprite component
        self.sprite = cocos.sprite.Sprite(anims['stand_south'])
        self.sprite.image_anchor = (0, 0)
        self.sprite.position = sprite_offset
        self.add(self.sprite)
        # Movement component
        self.action = self.do(move)
        self.move = self.actions[self.actions.index(self.action)]
        self.move.push_handlers(self)
        # Collide with actors and the collision map
        self.actor_collision = ActorCollisionComponent(self)
        self.map_collision = MapCollisionComponent(self)
        self.interact = InteractComponent(self, 10, 32)

    def on_enter(self):
        super(Character, self).on_enter()
        #self.parent.add_actor_collision(self.actor_collision)
        #self.parent.add_map_collision(self.map_collision)
        #self.parent.add_interact(self.interact)

    def on_exit(self):
        super(Character, self).on_exit()
        #self.parent.remove_actor_collision(self.actor_collision)
        #self.parent.remove_map_collision(self.map_collision)
        #self.parent.remove_interact(self.interact)

    def on_walk(self):
        self.update_animation()

    def on_stop(self):
        self.update_animation()

    def on_change_direction(self, direction):
        self.update_animation()

    def update_animation(self):
        prefix = 'walk_' if self.move.walking else 'stand_'
        self.sprite.image = self.anims[prefix + self.move.direction]

    def on_request_move(self, dx, dy):
        pass
        #x, y = self.x + dx, self.y + dy
        #if self.map_collision.check_collision(x, y) or self.actor_collision.check_collision(x, y):
        #    self.move.cancel_movement()



