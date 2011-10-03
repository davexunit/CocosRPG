import sys
import weakref

import pyglet
from pyglet.window import key, mouse

import cocos
from cocos import tiles, actions, layer, rect, scenes

class State(layer.Layer):
    '''State actors control the tile engine.
    State actors register input events and perform their specific task.
    Common tile engines states are: Walkaround, Dialog, and Cinematic
    Each State should perform a unique task.
    '''
    is_event_handler = True

class WalkaroundState(State):
    def __init__(self):
        super(WalkaroundState, self).__init__()
        self.input_component = None

    def on_enter(self):
        super(WalkaroundState, self).on_enter()
        if self.input_component:
            cocos.director.director.window.push_handlers(self.input_component)
    
    def on_exit(self):
        super(WalkaroundState, self).on_exit()
        if self.input_component:
            cocos.director.director.window.remove_handlers(self.input_component)

    def on_key_press(self, key, modifier):
        from ..game import game
        if key == game.config.get_keycode('use'):
            # Entity to possibly interact with
            entity = None
            player = self.input_component.owner
            # Translate hitbox up, down, left, or right depending on player direction
            player_rect = player.get_rect()
            sprite = player.get_component('graphics')

            if sprite.direction == 'north':
                player_rect.y += player_rect.height
            elif sprite.direction == 'south':
                player_rect.y -= player_rect.height
            elif sprite.direction == 'east':
                player_rect.x += player_rect.width
            elif sprite.direction == 'west':
                player_rect.x -= player_rect.width
            # Check for entities with dialog
            for s in self.parent.actors.get_actors():
                rect = s.get_rect()
                if s != player and rect.intersects(player_rect) :
                    entity = s
                    break
            if entity != None:
                #entity.on_interact(player)
                input = player.get_component('input')
                input.stop_moving()
                if entity.has_component('dialog'):
                    self.parent.state_push(DialogState(entity.get_component('dialog').text))

    def on_mouse_press (self, x, y, buttons, modifiers):
        '''This is just to test some stuff. Should be removed at some point.
        '''
        '''# Add a sprite to screen at the mouse location on right click
        if buttons & mouse.RIGHT:
            new_sprite = create_sprite('new', *self.parent.map_layer.pixel_from_screen(x, y))
            self.parent.map_layer['actors'].add_object(new_sprite)
        # Left click changes sprite that player is controlling
        elif buttons & mouse.LEFT:
            for s in self.parent.map_layer['actors'].get_actors():
                if isinstance(s, Character) and s.get_rect().contains(*self.parent.map_layer.pixel_from_screen(x, y)):
                    self.parent.player.remove_action(self.action)
                    self.parent.player = s
                    self.action = self.parent.player.do(MovePlayer())
                    break
        '''

class DialogState(State):
    def __init__(self, text):
        super(DialogState, self).__init__()
        self.dialog_layer = self._make_dialog_layer()
        self.text = text
        self.font_name = 'Sans'
        self.font_size = 12
        self.label = self._make_label()
        self.dialog_layer.add(self.label, name='label')

    def _make_label(self):
        label = cocos.text.Label(self.text, font_name=self.font_name, font_size=self.font_size, multiline=True, width=self.dialog_layer.px_width - self.dialog_layer.tw*2)
        label.position = (self.dialog_layer.tw, self.dialog_layer.px_height - self.dialog_layer.th) 
        label.element.anchor_y = 'top'
        return label
 
    def _make_dialog_layer(self):
        # Load dialog box border
        image = pyglet.resource.image('Dialog_Border.png')
        # The border is a 3x3 tile grid
        grid = pyglet.image.ImageGrid(image, 3, 3)
        # The width of the dialog box will be the width of the window
        w = cocos.director.director.get_window_size()[0]
        # Calculate how many tiles can fit in the space we have to fill
        num_columns, num_rows = w / grid.item_width, 128 / grid.item_height
        # Construct rectmap that creates a dialog box border
        columns = list()
        for i in range(0, num_columns):
            row = list()
            columns.append(row)
            # Ugly as sin
            for j in range(0, num_rows):
                if i == 0 and j == 0:
                    index = 0
                elif i == 0 and j == num_rows - 1:
                    index = 6
                elif i == num_columns - 1 and j == 0:
                    index = 2
                elif i == num_columns - 1 and j == num_rows - 1:
                    index = 8
                elif i == 0 and j != 0 and j != num_rows - 1:
                    index = 3
                elif i == num_columns - 1 and j != 0 and j != num_rows - 1:
                    index = 5
                elif i != 0 and i != num_columns - 1  and j == 0:
                    index = 1
                elif i != 0 and i != num_columns - 1  and j == num_rows - 1:
                    index = 7
                else:
                    index = 4
                tile = cocos.tiles.Tile(1, None, grid[index])
                row.append(cocos.tiles.RectCell(i, j, grid.item_width, grid.item_height, None, tile))
        dialog_layer = cocos.tiles.RectMapLayer('Dialog', grid.item_width, grid.item_height, columns, (0,0,0), None)
        # Set the view of the dialog box to exactly the size of the dialog box
        dialog_layer.set_view(0, 0, dialog_layer.px_width, dialog_layer.px_height)
        return dialog_layer

    def on_enter(self):
        super(DialogState, self).on_enter()
        self.parent.add(self.dialog_layer, z=1)

    def on_exit(self):
        super(DialogState, self).on_exit()
        self.parent.remove(self.dialog_layer)

    def on_key_press(self, key, modifier):
        if key == pyglet.window.key.SPACE:
            self.parent.state_pop()

class CinematicState(State):
    pass

class ActorLayer(cocos.layer.ScrollableLayer):
    def __init__(self, id=''):
        super(ActorLayer, self).__init__()
        self.id = id
        self.actors = {}
        self.map_scene = None
        self.batch = cocos.batch.BatchNode()
        self.add(self.batch)

    @property
    def map_scene(self):
        if self._map_scene == None:
            return None

        return self._map_scene()

    @map_scene.setter
    def map_scene(self, new_map_scene):
        if new_map_scene == None:
            self._map_scene = None
        else:
            self._map_scene = weakref.ref(new_map_scene)

        for a in self.actors.values():
            a.parent_map = new_map_scene

    def add_actor(self, actor):
        self.actors[actor.name] = actor

        if self.map_scene != None:
            actor.parent_map = self.map_scene

        if actor.has_component('graphics'):
            self.batch.add(actor.get_component('graphics').sprite)

        actor.on_enter()
    
    def remove_actor(self, actor):
        del self.actors[actor.name]
        actor.parent_map = None

        if actor.has_component('graphics'):
            self.batch.remove(actor.get_component('graphics').sprite)

        actor.on_exit()

    def get_actor(self, name):
        return self.actors[name]

    def get_actors(self):
        return self.actors.values()

    def get_in_region(self, rect):
        actors = weakref.WeakSet()
        for a in self.actors.values():
            actor_rect = cocos.rect.Rect(a.x, a.y, a.width, a.height)
            if actor_rect.intersects(rect):
                actors.add(a)
        return actors

    def update(self, dt):
        for actor in self.actors.values():
            actor.update(dt)

class MapScene(cocos.scene.Scene):
    def __init__(self, width, height, tile_width, tile_height):
        super(MapScene, self).__init__()
        self.name = "Nowhere"
        # Map dimensions in tiles
        self.map_width = width
        self.map_height = height
        self.map_size = (width, height)
        # Tile dimensions in pixels
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.tile_size = (tile_width, tile_height)
        # State
        self.state = list()
        # Actor to focus on
        self.focus = None

    def on_enter(self):
        super(MapScene, self).on_enter()
        self.schedule(self.update)
        #from sys import getrefcount
        #print "enter: " + str(getrefcount(self))

    def on_exit(self):
        super(MapScene, self).on_exit()
        self.unschedule(self.update)
        #from sys import getrefcount
        #print "exit: " + str(getrefcount(self))

    def update(self, dt):
        self.actors.update(dt)

    def do_focus(self):
        if self.focus != None:
            self.scroller.set_focus(self.focus.x, self.focus.y)

    def visit(self):
        # For some reason this is the only way to the map scroll smoothly
        self.do_focus()
        super(MapScene, self).visit()

    def init_layers(self, ground, fringe, over, collision, actors):
        # Set member variables
        self.ground = ground
        self.fringe = fringe
        self.over = over
        self.collision = collision
        self.actors = actors
        self.actors.map_scene = self
        # Create a scrolling manager for the map layers
        self.scroller = cocos.layer.ScrollingManager()
        self.scroller.add(self.ground, name='ground', z=0)
        self.scroller.add(self.fringe, name='fringe', z=1)
        self.scroller.add(self.actors, name='actors', z=2)
        self.scroller.add(self.over, name='over', z=3)
        self.add(self.scroller, name='scroller')

    def state_replace(self, new_state):
        # Remove old state is there was one and suppress the exception
        try:
            self.remove(self.state.pop())
        except IndexError:
            pass
        self.state_push(new_state)

    def state_push(self, new_state):
        # Push new state
        try:
            self.remove(self.state[-1])
        except:
            pass
        self.state.append(new_state)
        self.add(new_state)

    def state_pop(self):
        self.remove(self.state.pop())
        self.add(self.state[-1])
