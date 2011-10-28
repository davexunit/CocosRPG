import config
import sqlite3
import pyglet

class Game(object):
    '''The Game class contains all of the game's global state. Yeah, yeah,
    global is state is bad. Blah blah blah. But this is the easiest way to have
    a universally accessible dataset containing things like the sqlite database
    connection, configuration details, and player stats.
    '''
    def __init__(self):
        self.db = None
        self.config = None

        # Add resource file paths
        pyglet.resource.path.append('data')
        pyglet.resource.path.append('data/images')
        pyglet.resource.path.append('data/maps')
        pyglet.resource.path.append('data/anims')
        pyglet.resource.path.append('data/sounds')
        pyglet.resource.reindex()


    def load_config(self, filename):
        self.config = config.GameConfig(filename)

    def load_db(self, filename):
        self.db = sqlite3.connect(filename)
        self.db.row_factory = sqlite3.Row

# Global game instance
game = Game()
