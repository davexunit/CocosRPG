import pyglet

class Component(pyglet.event.EventDispatcher):
    '''Components provide functionality to Actors. Components avoid the deep
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
        '''This method is to be called only by the Actor class. If you are
        to call this method manually, you must also manually remove the
        component from the Actor's dictionary. In other words, don't do
        this. Use Actor.remove_component instead.
        '''
        self.owner = None
        self.on_detach()

    def on_refresh(self):
        '''This method is called by the Actor class when the component
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
class SpriteComponent(Component):
    '''Graphics component that displays an animated sprite.
    '''
    component_type = "graphics"

    def __init__(self, anims):
        super(SpriteComponent, self).__init__()
        self.sprite = cocos.sprite.Sprite(anims['stand_south'], anchor=(0,0))
        # Offset the sprite from the actor's hitbox
        self._dx, self._dy = 0, 0
        self.anims = anims
        self.walking = False
        self.direction = 'south'

    def on_refresh(self):
        self.owner.push_handlers(self)
        self.owner.get_component('physics').push_handlers(self)

    def on_move(self, x, y, rel_x, rel_y):
        self.sprite.position = (x - self._dx, y - self._dy)

    def update_animation(self):
        prefix = 'walk_' if self.walking else 'stand_'
        self.sprite.image = self.anims[prefix + self.direction]

    def on_direction_changed(self, dx, dy):
        if dx == 0 and dy == 0:
            self.walking = False
        else:
            self.walking = True

        if dx > 0:
            self.direction = 'east'
        elif dx < 0:
            self.direction = 'west'
        elif dy > 0:
            self.direction = 'north'
        elif dy < 0:
            self.direction = 'south'
        self.update_animation()

import math
class HumanInputComponent(Component):
    '''Input component that takes input from the keyboard.
    '''
    component_type = "input"

    def __init__(self):
        super(HumanInputComponent, self).__init__()
        cocos.director.director.window.push_handlers(self)

    def on_refresh(self):
        self.physics = self.owner.get_component('physics')

    def on_key_press(self, key, modifiers):
        if key == pyglet.window.key.UP:
            self.physics.dy += 1.0
        elif key == pyglet.window.key.DOWN:
            self.physics.dy -= 1.0
        elif key == pyglet.window.key.RIGHT:
            self.physics.dx += 1.0
        elif key == pyglet.window.key.LEFT:
            self.physics.dx -= 1.0

    def on_key_release(self, key, modifiers):
        if key == pyglet.window.key.UP:
            self.physics.dy -= 1.0
        elif key == pyglet.window.key.DOWN:
            self.physics.dy += 1.0
        elif key == pyglet.window.key.RIGHT:
            self.physics.dx -= 1.0
        elif key == pyglet.window.key.LEFT:
            self.physics.dx += 1.0

import pyglet
class PhysicsComponent(Component):
    component_type = "physics"

    def __init__(self):
        super(PhysicsComponent, self).__init__()
        self._dx, self._dy = 0, 0
        self.speed = 300
        self.collidable = True
        pyglet.clock.schedule(self.do_move)

    @property
    def dx(self):
        return self._dx

    @dx.setter
    def dx(self, newdx):
        self._dx = newdx
        self.dispatch_event('on_direction_changed', self._dx, self._dy)

    @property
    def dy(self):
        return self._dy

    @dy.setter
    def dy(self, newdy):
        self._dy = newdy
        self.dispatch_event('on_direction_changed', self._dx, self._dy)

    @property
    def direction(self):
        return (self._dx, self._dy)

    @direction.setter
    def direction(self, dir):
        self._dx, self._dy = dir
        self.dispatch_event('on_direction_changed', self._dx, self._dy)

    def do_move(self, dt):
        # Normalize direction vector
        mag = math.sqrt((self._dx * self._dx) + (self._dy * self._dy))
        if mag != 0:
            ndx, ndy = self._dx / mag, self._dy / mag
        else:
            ndx, ndy = 0, 0

        # Calculate movement
        move_x = self._dx * self.speed * dt
        move_y = self._dy * self.speed * dt

        # Check collision on X axis
        rect = self.owner.get_rect()
        rect.x += move_x
        collide_x = self.check_collision(rect)

        # Check collision on Y axis
        rect = self.owner.get_rect()
        rect.y += move_y
        collide_y = self.check_collision(rect)

        # Move actor
        if not collide_x:
            self.owner.x += move_x

        if not collide_y:
            self.owner.y += move_y

        # Dispatch collision event if collision occurred
        if collide_x or collide_y:
            self.dispatch_event('on_collision')

    def check_collision(self, rect):
        # Ignore collision test if collidable flag is not set
        if not self.collidable:
            return False

        # Check map collision
        for cell in self.owner.parent_map.collision.get_in_region(*(rect.bottomleft + rect.topright)):
            if cell.tile != None:
                return True

        return False

# Events for PhysicsComponent
PhysicsComponent.register_event_type('on_collision')
PhysicsComponent.register_event_type('on_direction_changed')

class PlayerSoundComponent(Component):
    component_type = "sound"

    def __init__(self):
        super(PlayerSoundComponent, self).__init__()
        self.collision = pyglet.resource.media('snare.wav', streaming=False)
        self.play_collision = True

    def on_refresh(self):
        self.owner.get_component('physics').push_handlers(self)

    def on_collision(self):
        if self.play_collision:
            self.collision.play()
            self.play_collision = False
            def activate_sound(dt):
                self.play_collision = True
            pyglet.clock.schedule_once(activate_sound, .5)

