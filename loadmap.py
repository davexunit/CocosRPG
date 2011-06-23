try:
    from xml.etree import ElementTree
except ImportError:
    import elementtree.ElementTree as ElementTree

import os
import base64
import zlib
import array
import pyglet
from pyglet.gl import *
import cocos
import entity

class TileSet(list):
    pass

class MapException(Exception):
    pass

def load_map(filename):
    tree = ElementTree.parse(filename)
    root = tree.getroot()

    # Root level tag is expected to be <map> so raise an exception if it's not
    if root.tag != 'map':
        raise MapException('%s root level tag is %s rather than <map>' % (filename, root.tag))
    # We can only orthogonal maps here because that's all I care about
    if root.get('orientation') != 'orthogonal':
        raise MapException('Map orientation %s not supported. Orthogonal maps only' % root.get('orientation'))

    # Get map properties
    width = int(root.get('width'))
    height = int(root.get('height'))
    tile_width = int(root.get('tilewidth'))
    tile_height = int(root.get('tileheight'))

    # Load tilesets
    tileset = TileSet()
    for tag in root.findall('tileset'):
        tileset += load_tileset(tag)
    # Load layers
    layers = dict()
    for tag in root.findall('layer'):
        layer = load_layer(tag, tileset, tile_width, tile_height)
        layers[layer.id] = layer
    # Load object layers
    for tag in root.findall('objectgroup'):
        layer = load_object_layer(tag)
        layers[layer.id] = layer
    return layers

def load_tileset(tag):
    # Get tileset properties
    firstgid = int(tag.get('firstgid'))
    name = tag.get('name')
    tile_width = int(tag.get('tilewidth'))
    tile_height = int(tag.get('tileheight'))

    child = tag.find('image')
    # Raise an exception if child tag is not <image>
    if child.tag != 'image':
        raise MapException('Unsupported tag in tileset: %s' % child.tag)
    # Load image
    image, image_width, image_height  = load_image(child)

    # Construct tileset
    #tileset = cocos.tiles.TileSet(name, None)
    tileset = TileSet()
    for y in range(0, image_height, tile_height):
        for x in range(0, image_width, tile_width):
            tile = image.get_region(x, image_height - y - tile_height, tile_width, tile_height)
            #tileset.add(None, tile)
            tileset.append(cocos.tiles.Tile(y * (image_width / tile_width) + x, None, tile))
            # set texture clamping to avoid mis-rendering subpixel edges
            # Taken from cocos2d tiles.py
            # BSD licensed
            tile.texture.id
            glBindTexture(tile.texture.target, tile.texture.id)
            glTexParameteri(tile.texture.target, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(tile.texture.target, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    return tileset

def load_image(tag):
    # Get image properties
    source = tag.get('source')
    width = int(tag.get('width'))
    height = int(tag.get('height'))

    return pyglet.resource.image(source), width, height

def load_layer(tag, tileset, tile_width, tile_height):
    # Get layer properties
    name = tag.get('name')
    width = int(tag.get('width'))
    height = int(tag.get('height'))

    child = tag.find('data')
    # Raise exception if there is no <data> tag because that's fucked up
    if child == None:
        raise MapException('No <data> tag in layer')
    # Load layer data
    data = load_data(child)
    # Construct layer
    columns = []
    for i in range(0, width):
        row = []
        columns.append(row)
        for j in range(0, height):
            index = j * width + i
            tile = tileset[data[index] - 1]
            if data[index] == 0:
                tile = None
            row.insert(0, cocos.tiles.RectCell(i, height - j - 1, tile_width, tile_height, None, tile))
    return cocos.tiles.RectMapLayer(name, tile_width, tile_height, columns, (0,0,0), None)

def load_data(tag):
    # Get data properties
    encoding = tag.get('encoding')
    compression = tag.get('compression')
    data = tag.text

    # Only base64 encoding supported as of now
    if encoding != 'base64':
        raise MapException('Encoding type %s not supported' % encoding)
    # Only zlib compression supported as of now
    if compression != 'zlib':
        raise MapException('Compression type %s not supported' % compression)

    # Uncompress data
    decoded_data = zlib.decompress(base64.b64decode(data))
    # decoded_data is a string made of 64 bit integers now
    # Turn that string into an array of 64 bit integers
    return array.array('L', decoded_data)

def load_object_layer(tag):
    name = tag.get('name')
    width = int(tag.get('width'))
    height = int(tag.get('height'))
    layer = entity.ObjectLayer(name)
    for child in tag.findall('object'):
        layer.add_object(load_object(child))
    return layer

def load_object(tag):
    # Get object properties
    name = tag.get('name')
    type = tag.get('type')
    x = int(tag.get('x'))
    y = int(tag.get('y'))
    width = int(tag.get('width'))
    height = int(tag.get('height'))
    properties = dict()
    for p in tag.find('properties'):
        properties[p.get('name')] = p.get('value')
    # Factory
    if type == 'portal':
        return load_portal(properties, name, cocos.rect.Rect(x, y, width, height))
    else:
        raise MapException('Object type %s not supported' % type)

def load_portal(properties, name, rect):
    map_file = properties['map']
    spawn = properties['spawn'].split(',')

# Test
if __name__ == '__main__':
    from cocos.director import director
    from cocos import layer
    from pyglet.window import key

    class MovePlayer(cocos.actions.Move):
        def step(self, dt):
            speed = 300
            dx = (keyboard[key.RIGHT] - keyboard[key.LEFT]) * speed
            dy = (keyboard[key.UP] - keyboard[key.DOWN]) * speed
            vert = self.target.get_rect()
            vert.y += dy * dt
            hor = self.target.get_rect()
            hor.x += dx * dt
            if self.check_collision(vert):
                dy = 0
            if self.check_collision(hor):
                dx = 0
            self.target.velocity = (dx, dy)
            super(MovePlayer, self).step(dt)
            scroller.set_focus(self.target.x, self.target.y)
        
        def check_collision(self, rect):
            for cell in collision_layer.get_in_region(*(rect.bottomleft + rect.topright)):
                if cell.tile != None:
                    return True
            return False

    director.init(width=640, height=480, do_not_scale=True, resizable=True)
    director.show_FPS = True

    keyboard = key.KeyStateHandler()
    director.window.push_handlers(keyboard)

    # Load map
    map_layers = load_map('inn.tmx')

    # Load a map and put it in a scrolling layer
    scroller = layer.ScrollingManager()
    ground_layer = map_layers['ground']
    fringe_layer = map_layers['fringe']
    over_layer = map_layers['over']
    collision_layer = map_layers['collision']
    scroller.add(ground_layer, z=0)
    scroller.add(fringe_layer, z=1)
    scroller.add(over_layer, z=3)

    player_layer = layer.ScrollableLayer()
    player = cocos.sprite.Sprite('king_single.png')
    player.do(MovePlayer())
    player.position = 16, 200
    player_layer.add(player)
    scroller.add(player_layer, z=2)

    # Create the main scene
    main_scene = cocos.scene.Scene(scroller)

    # Run game
    director.run(main_scene)
