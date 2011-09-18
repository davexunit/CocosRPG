import pyglet

class Component(pyglet.event.EventDispatcher):
    '''Components provide functionality to MapActors. Components avoid the deep
    hierarchy inheritance problem with game objects that share functionality.
    Components should do one thing only and do it well. Components talk to each
    other by using the pyglet event framework. Alternatively, components can
    obtain direct references to other components if needed.
    '''
    # Class level variable containing a string with the Component's type
    # string. Child classes must set this variable.
    component_type = None

    def __init__(self):
        self.owner = None

    def attach(self, actor):
        '''Sets the owner of this component to the given actor. An exception
        will be raised if this component is already owned by someone else.
        '''
        if self.owner != None:
            raise Exception("Component of type %s already has an owner" %
                    self.type)
        self.owner = actor

    def detach(self):
        '''This method is to be called only by the MapActor class. If you are
        to call this method manually, you must also manually remove the
        component from the MapActor's dictionary. In other words, don't do
        this. Use MapActor.remove_component instead.
        '''
        self.owner = None

        self.on_detach()

    def on_refresh(self):
        '''This method is called by the MapActor class when the component
        'wiring' needs to be refreshed. Use this method to perform all event
        registering and direct reference storing to other components.
        '''
        pass

    def on_detach(self):
        '''When detached (removed by the owner), a well-behaved component will
        unregister all events that it was previously registered to and do
        whatever else it needs to do.
        '''
        pass

import cocos
class SpriteComponent(Component, cocos.sprite.Sprite):
    '''Graphics component that displays an animated sprite.
    '''
    component_type = "graphics"

    def __init__(self, image_file):
        super(SpriteComponent, self).__init__(image_file)


