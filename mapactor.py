class MapActor(object):
    '''MapActors represent any object on the map that isn't a tile. This class
    is simply a container of components. Mix and match components to create the
    MapActors that you need.
    '''
    def __init__(self):
        super(MapActor, self).__init__()
        self.name = "Anonymous"
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.parent_map = None
        self.components = {}

    @property
    def position(self):
        return (self.x, self.y)

    @position.setter
    def position(self, position):
        self.x, self.y = position
        
    @property
    def size(self):
        return (self.width, self.height)

    @size.setter
    def size(self, size):
        self.width, self.height = size

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
        into the events of other components that belong to the MapActor.
        You should call this once during the initial creation of the MapActor,
        after all of the components have been added.
        If you add/remove components later, make sure to refresh.
        '''
        for component in self.components.values():
            component.on_refresh()

class Player(MapActor):
    def __init__():
        super(MapActor, self).__init__()
        self.add_component(HumanInputComponent())
        self.add_component(SpriteComponent())
        self.add_component(CollisionComponent())
        self.refresh_components()
