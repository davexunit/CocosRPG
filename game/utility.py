import os
import pyglet

def resource_path(filename):
    return os.path.join(pyglet.resource.location(filename).path, filename)

