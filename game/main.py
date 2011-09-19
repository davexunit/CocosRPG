import sqlite3
import utility
import mapload
from map.mapscene import *
from actor import actor
from cocos.director import director

def main():
    director.init(width=640, height=480, do_not_scale=True, resizable=True)
    director.show_FPS = True

    # Load database
    db = sqlite3.connect(utility.resource_path('database'))

    # Load map scene
    map_scene = mapload.load_map('outside.tmx', db)
    map_scene.state_replace(WalkaroundState())

    # Setup player sprite
    player = actor.Player()
    player.position = (440, 200)

    # Add player to map
    map_scene.actors.add_actor(player)
    map_scene.focus = player

    # Add retarded NPCs
    import random
    random.seed()
    for i in range(100):
        npc = actor.Derp()
        npc.position = (random.randint(0, 1000), random.randint(0, 1000))
        map_scene.actors.add_actor(npc)

    # Run map scene
    director.run(map_scene)
