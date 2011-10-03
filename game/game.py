import config

class Game(object):
    '''The Game class contains all of the game's global state. Yeah, yeah,
    global is state is bad. Blah blah blah. But this is the easiest way to have
    a universally accessible dataset containing things like the sqlite database
    connection, configuration details, and player stats.
    '''
    def __init__(self):
        self.db = None
        self.config = None

    def load_config(self, filename):
        self.config = config.GameConfig(filename)

# Global game instance
game = Game()
