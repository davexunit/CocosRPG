import pyglet
import cocos

class Actor(pyglet.event.EventDispatcher):
    '''Actors represent any object on the map that isn't a tile. This class
    is simply a container of components. Mix and match components to create the
    Actors that you need.
    '''
    def __init__(self):
        super(Actor, self).__init__()
        self.name = "Anonymous"
        self.group = None
        self._x = 0
        self._y = 0
        self.width = 0
        self.height = 0
        self.parent_map = None
        self.components = {}

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, newx):
        dx = newx - self._x
        self._x = newx
        self.dispatch_event('on_move', self._x, self._y, dx, 0)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, newy):
        dy = newy - self._y
        self._y = newy
        self.dispatch_event('on_move', self._x, self._y, 0, dy)

    @property
    def position(self):
        return (self._x, self._y)

    @position.setter
    def position(self, position):
        newx, newy = position
        dx, dy = newx - self._x, newy - self._y
        self._x, self._y = newx, newy
        self.dispatch_event('on_move', self._x, self._y, dx, dy)
        
    @property
    def size(self):
        return (self.width, self.height)

    @size.setter
    def size(self, size):
        self.width, self.height = size
    
    def get_rect(self):
        return cocos.rect.Rect(self._x, self._y, self.width, self.height)

    def add_component(self, component):
        '''Adds a component to the component dictionary. If a component of the same type is
        already attached, it will be detached and replaced by the new one.
        '''
        t = component.component_type

        # Run clean-up on previous component of the same type
        if t in self.components:
            self.remove_component(t)

        # Add new component
        self.components[t] = component
        component.attach(self)

    def remove_component(self, component_type):
        '''Detaches component of the given type and calls the necessary
        clean-up routines. A KeyError will be raised if a component of given
        type is not attached.
        '''
        self.components[component_type].detach()

    def has_component(self, component_type):
        '''Tests if a component of given type is attached.
        '''
        return component_type in self.components

    def get_component(self, component_type):
        '''Retrieves reference to the component of the given type. A KeyError
        will be raised if there is no component of that type.
        '''
        return self.components[component_type]

    def refresh_components(self):
        '''Refreshing the components gives each component the chance to hook
        into the events of other components that belong to the Actor.
        You should call this once during the initial creation of the Actor,
        after all of the components have been added.
        If you add/remove components later, make sure to refresh.
        '''
        for component in self.components.values():
            component.on_refresh()

# Event handlers for Actor
Actor.register_event_type('on_move')

from component import *
from .. import mapload
class Player(Actor):
    def __init__(self):
        super(Player, self).__init__()
        self.size = (24, 24)

        # Load animations
        anims = mapload.load_animset('king.xml')

        self.add_component(HumanInputComponent())
        self.add_component(SpriteComponent(anims, offset=(-4,0)))
        self.add_component(PhysicsComponent(200))
        self.add_component(PlayerSoundComponent())
        self.refresh_components()

class Derp(Actor):
    def __init__(self):
        super(Derp, self).__init__()
        self.size = (24, 24)

        # Load animations
        from .. import mapload
        anims = mapload.load_animset('king.xml')

        self.add_component(DumbAI())
        self.add_component(SpriteComponent(anims, offset=(-4,0)))
        self.add_component(PhysicsComponent(200))
        self.refresh_components()

class Sign(Actor):
    def __init__(self, text):
        super(Sign, self).__init__()
        self.add_component(DialogComponent(text))
        self.add_component(PhysicsComponent(200))
        self.refresh_components()

@mapload.register_actor_factory("sign")
def load_sign(mapscene, width, height, properties):
    sign = Sign(properties['text'])
    sign.size = (width, height)
    return sign
@mapload.register_actor_factory("portal")
def load_portal(mapscene, width, height, properties):
    return Actor()
