import ConfigParser
import pyglet

config = ConfigParser.RawConfigParser()
config.read("rpg.conf")

def keycode(name):
    return eval("pyglet.window.key." + config.get('Controls', name))
