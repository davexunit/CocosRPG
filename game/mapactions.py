import cocos
import pyglet
import copy

class Move(cocos.actions.Move, pyglet.event.EventDispatcher):
    def __deepcopy__(self, memo):
        return copy.copy(self)

    def init(self, speed):
        self.speed = speed
        self.direction = (0, 0)

    def start(self):
        self.target.velocity = (0, 0)

    def set_direction(self, vector):
        self.direction = tuple(vector)
        self.dispatch_event('on_change_direction', vector)

    def on_map_collision(self, collide_x, collide_y):
        vx, vy = self.target.velocity
        if collide_x:
            vx = 0
        if collide_y:
            vy = 0
        self.target.velocity = (vx, vy)

    def step(self, dt):
        # Request movement (movement can be stopped by event handler)
        dx, dy = self.direction
        self.target.velocity = (dx * self.speed, dy * self.speed)
        vx, vy = self.target.velocity
        if vx != 0 or vy != 0:
            self.dispatch_event('on_request_move', self.target.x + vx * dt, self.target.y + vy * dt)
        # Super!!!!!!
        super(Move, self).step(dt)
        self.target.position = int(self.target.x), int(self.target.y)
        # If movement hasn't been stopped then dispatch on_move event
        vx, vy = self.target.velocity
        if vx != 0 or vy != 0:
            self.dispatch_event('on_move', self.target.x, self.target.y)
Move.register_event_type('on_change_direction')
Move.register_event_type('on_request_move')
Move.register_event_type('on_move')

class EventAction(cocos.actions.Action, pyglet.event.EventDispatcher):
    def __deepcopy__(self, memo):
        return copy.copy(self)

class Input(cocos.actions.Action):
    def init(self, move):
        self.move = move

class PlayerInput(Input):
    def init(self, move):
        super(PlayerInput, self).init(move)
        self.vx, self.vy = 0, 0
        cocos.director.director.window.push_handlers(self)

    def on_key_press(self, key, modifiers):
        if key == pyglet.window.key.UP:
            self.vy += 1
        elif key == pyglet.window.key.DOWN:
            self.vy -= 1
        elif key == pyglet.window.key.LEFT:
            self.vx -= 1
        elif key == pyglet.window.key.RIGHT:
            self.vx += 1
        self.move.set_direction((self.vx, self.vy))

    def on_key_release(self, key, modifiers):
        if key == pyglet.window.key.UP:
            self.vy -= 1
        elif key == pyglet.window.key.DOWN:
            self.vy += 1
        elif key == pyglet.window.key.LEFT:
            self.vx += 1
        elif key == pyglet.window.key.RIGHT:
            self.vx -= 1
        self.move.set_direction((self.vx, self.vy))

class DumbAI(Input):
    def init(self, move, follow):
        super(DumbAI, self).init(move)
        self.follow = follow

    def step(self, dt):
        vx, vy = 0, 0
        if self.follow.x > self.target.x:
            vx = 1
        elif self.follow.x < self.target.x:
            vx = -1
        if self.follow.y > self.target.y:
            vy = 1
        elif self.follow.y < self.target.y:
            vy = -1
        self.move.set_direction((vx, vy))

class CharacterAnimation(EventAction):
    def init(self, anims):
        self.anims = anims
        self.walking = False
        self.direction = 'south'

    def start(self):
        self.update_animation()

    def update_animation(self):
        prefix = 'walk_' if self.walking else 'stand_'
        self.target.sprite.image = self.anims[prefix + self.direction]

    def on_change_direction(self, vector):
        if vector == (0, 0):
            self.walking = False
        else:
            self.walking = True
        if vector == (1, 0):
            self.direction = 'east'
        elif vector == (-1, 0):
            self.direction = 'west'
        elif vector == (0, 1):
            self.direction = 'north'
        elif vector == (0, -1):
            self.direction = 'south'
        self.update_animation()

class CameraFocus(cocos.actions.Action):
    def __deepcopy__(self, memo):
        return copy.copy(self)

    def init(self, mapscene):
        self.mapscene = mapscene

    def step(self, dt):
        super(CameraFocus, self).step(dt)
        self.mapscene.scroller.set_focus(self.target.x, self.target.y)

class MapCollision(EventAction):
    def init(self):
        self.collidable = True

    def on_request_move(self, x, y):
        # Check collision on X axis
        rect = cocos.rect.Rect(x, self.target.y, self.target.width, self.target.height)
        collide_x = self.check_collision(rect)
        # Check collision on Y axis
        rect = cocos.rect.Rect(self.target.x, y, self.target.width, self.target.height)
        collide_y = self.check_collision(rect)
        # Dispatch collision event if collision occurred
        if collide_x or collide_y:
            self.dispatch_event('on_map_collision', collide_x, collide_y)

    def check_collision(self, rect):
        # Ignore collision test if collidable flag is not set
        if not self.collidable:
            return False
        for cell in self.target.map_scene.collision.get_in_region(*(rect.bottomleft + rect.topright)):
            if cell.tile != None:
                return True
        return False
MapCollision.register_event_type('on_map_collision')

class Trigger(EventAction):
    def init(self, map_scene):
        self.map_scene = map_scene
        self.enabled = True
        self.actors = list()
    
    def step(self, dt):
        if not self.enabled:
            return
        new_actors = self.map_scene.actors.get_in_region(cocos.rect.Rect(self.target.x, self.target.y, self.target.width, self.target.height))
        new_actors.remove(self.target)
        for a in new_actors:
            if a not in self.actors:
                self.dispatch_event('on_enter', a)
        for a in self.actors:
            if a not in new_actors:
                self.dispatch_event('on_exit', a)
        self.actors = new_actors
Trigger.register_event_type('on_enter')
Trigger.register_event_type('on_exit')
