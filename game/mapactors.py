import pyglet
import cocos
import mapload
from mapactions import *

class MapActor(cocos.cocosnode.CocosNode):
    def __init__(self, width, height):
        super(MapActor, self).__init__()
        self.width = width
        self.height = height
        self.map_scene = None
        
    @property
    def size(self):
        return (self.width, self.height)

    @size.setter
    def size(self, size):
        self.width, self.height = size

    def do(self, action, target=None):
        new_action = super(MapActor, self).do(action, target)
        # If the action is an EventDispatcher, we need to hook the events together.
        #if instanceof(new_action, 

def make_player(mapscene, anims):
    player = MapActor(24, 32)
    player.name = 'Player'
    sprite = cocos.sprite.Sprite(anims['stand_south'])
    sprite.image_anchor = (0, 0)
    sprite.position = (-6, 0)
    player.add(sprite)
    player.sprite = sprite
    collision = player.do(MapCollision())
    animate = player.do(CharacterAnimation(anims))
    move = Move(200)
    #move.push_handlers(move)
    #move.push_handlers(animate)
    #move.push_handlers(collision)
    move = player.do(move)
    #collision.push_handlers(move)
    keyboard = PlayerInput(move)
    player.do(keyboard)
    return player

def make_portal(map_scene, width, height, map_file):
    portal = MapActor(width, height)
    trigger = Trigger(map_scene)
    def on_enter(actor):
        new_scene = mapload.load_map(map_file, None)
        new_scene.actors.add_actor(actor)
        cocos.director.director.replace(new_scene)
    trigger.push_handlers(on_enter)
    portal.do(trigger)
    return portal

@mapload.register_actor_factory('portal')
def portal(map_scene, width, height, properties):
    map_file = properties['map']
    return make_portal(map_scene, width, height, map_file)

def make_sign(width, height):
    sign = MapActor(width, height)
    return sign

@mapload.register_actor_factory('sign')
def sign(mapscene, width, height, properties):
    return make_sign(width, height)
