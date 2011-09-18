if __name__ == "__main__":
    import pyglet

    # Add resource file paths
    pyglet.resource.path.append('data')
    pyglet.resource.path.append('data/images')
    pyglet.resource.path.append('data/maps')
    pyglet.resource.path.append('data/anims')
    pyglet.resource.path.append('data/sounds')
    pyglet.resource.reindex()

    import game.main
    game.main.main()
