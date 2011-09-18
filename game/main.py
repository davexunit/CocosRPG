def main():
    import sqlite3
    import utility
    import mapload
    import mapactor
    import component
    from mapscene import *
    from cocos.director import director
    director.init(width=640, height=480, do_not_scale=True, resizable=True)
    director.show_FPS = True

    # Load database
    db = sqlite3.connect(utility.resource_path('database'))

    # Load map scene
    map_scene = mapload.load_map('outside.tmx', db)
    map_scene.state_replace(WalkaroundState())

    # Load animations
    anims = mapload.load_animset('king.xml')

    # Setup player sprite
    player = mapactor.Player()
    player.position = (200, 200)

    # Add player to map
    map_scene.actors.add_actor(player)

    # Run map scene
    director.run(map_scene)
