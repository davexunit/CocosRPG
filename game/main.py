import sqlite3
import utility
import mapload
from config import config
from map.mapscene import *
from actor import actor
from cocos.director import director
import weakref

def main():
    director.init(width=config.getint("Graphics", "screen_width"),
            height=config.getint("Graphics", "screen_height"),
            do_not_scale=True, resizable=True, 
            fullscreen=config.getboolean("Graphics", "fullscreen"))
    director.show_FPS = True

    # Load database
    db = sqlite3.connect(utility.resource_path('database'))

    # Load map scene
    def death(ref):
        print "map has died"
    map = mapload.load_map('outside.tmx', db)
    from sys import getrefcount
    #print getrefcount(map)
    map_scene = weakref.ref(map)
    #print getrefcount(map)
    walkaround = WalkaroundState()
    map_scene().state_replace(walkaround)

    # Setup player sprite
    player = actor.Player()
    player.name = "Dave"
    player.position = (460, 180)

    # Add player to map
    map_scene().actors.add_actor(player)
    map_scene().focus = player
    walkaround.input_component = player.get_component('input')

    # Add retarded NPCs
    '''
    import random
    random.seed()
    for i in range(50):
        npc = actor.Derp()
        npc.position = (random.randint(0, 1000), random.randint(0, 1000))
        map_scene.actors.add_actor(npc)
    '''

    #print "Start: %d" % (getrefcount(map),)
    # Run map scene
    director.run(map_scene())
