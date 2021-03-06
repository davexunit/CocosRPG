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

import util
from map import mapscene
from game import game

class TileSet(list):
    pass

class AnimSet(dict):
    pass

class MapException(Exception):
    pass

def load_animset(filename):
    # Open xml file
    root = ElementTree.parse(util.resource.resource_path(filename)).getroot()
    if root.tag != 'animset':
        raise MapException('Expected <animset> tag, found <%s> tag' % root.tag)

    # Get animset properties
    image = pyglet.resource.image('anims/' + root.get('image'))
    tile_width = int(root.get('tilewidth'))
    tile_height = int(root.get('tileheight'))

    # Create image sequence of tiles
    grid = pyglet.image.ImageGrid(image, image.width / tile_width, image.height / tile_height)
    sequence = grid.get_texture_sequence()
    anims = AnimSet()

    # Loop through all animations
    for child in root.findall('anim'):
        anim_name = child.get('name')
        anim_duration = float(child.get('duration'))
        frame_indices = [int(x) for x in child.text.split(',')]
        frames = list()
        for f in frame_indices:
            frames.append(sequence[f])
        anims[anim_name] = pyglet.image.Animation.from_image_sequence(frames, anim_duration, loop=True)
    return anims

def load_image(tag):
    # Get image properties
    source = tag.get('source')
    width = int(tag.get('width'))
    height = int(tag.get('height'))
    return pyglet.resource.image(source), width, height

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
    tileset = TileSet()
    for y in range(0, image_height, tile_height):
        for x in range(0, image_width, tile_width):
            tile = image.get_region(x, image_height - y - tile_height, tile_width, tile_height)
            tileset.append(cocos.tiles.Tile(y * (image_width / tile_width) + x, None, tile))
            # set texture clamping to avoid mis-rendering subpixel edges
            # Borrowed from cocos2d tiles.py
            tile.texture.id
            glBindTexture(tile.texture.target, tile.texture.id)
            glTexParameteri(tile.texture.target, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(tile.texture.target, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    return tileset

factories = dict()
def register_actor_factory(name):
    def decorate(func):
        factories[name] = func
        return func
    return decorate

def load_map(mapname):
    # Get map file from database
    cursor = game.db.cursor()
    cursor.execute('SELECT mapnum, file FROM map WHERE name=?', (mapname,))

    # Raise exception if the map is not found
    row = cursor.fetchone()
    if row == None:
        raise MapException('Map %s not found in database' % mapname)
    mapnum = row['mapnum']
    filename = row['file']

    # Open xml file
    tree = ElementTree.parse(util.resource.resource_path(filename))
    root = tree.getroot()

    # Root level tag is expected to be <map> so raise an exception if it's not
    if root.tag != 'map':
        raise MapException('%s root level tag is %s rather than <map>' % (filename, root.tag))
    # We can only load orthogonal maps here because that's all I care about :P
    if root.get('orientation') != 'orthogonal':
        raise MapException('Map orientation %s not supported. Orthogonal maps only' % root.get('orientation'))

    # Get map properties
    width = int(root.get('width'))
    height = int(root.get('height'))
    tile_width = int(root.get('tilewidth'))
    tile_height = int(root.get('tileheight'))

    # Create map scene
    map_scene = mapscene.MapScene(width, height, tile_width, tile_height)

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
        layer = load_actor_layer(map_scene, tag, tile_width, tile_height)
        layers[layer.id] = layer

    #layers['actors'] = mapscene.ActorLayer('actors')
    # Load actors from database
    load_from_db(layers['actors'], mapnum)

    map_scene.init_layers(layers['ground'], layers['fringe'], layers['over'], layers['collision'], layers['actors'])
    return map_scene
    
def load_from_db(layer, mapnum):
    # Get all actors in the map
    cursor = game.db.cursor()
    cursor.execute('SELECT actornum, type, name, group_name, x, y, width,\
            height FROM actor WHERE mapnum=?', (mapnum,))

    # Load all actors
    for row in cursor:
        # Query for all actor properties
        property_cursor = game.db.cursor()
        property_cursor.execute('SELECT property, value FROM actor_property\
            WHERE actornum=?', (row['actornum'],))

        # Make a dictionary of properties
        properties = {}
        for property_row in property_cursor:
            properties[property_row['property']] = property_row['value']

        actor = factories[row['type']](properties)
        actor.name = row['name']
        actor.group = row['group_name']
        actor.position = (int(row['x']), int(row['y']))
        actor.size = (int(row['width']), int(row['height']))
        layer.add_actor(actor)

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
    # TODO: Use encoding 'L' or 'I' accordingly based upon CPU architecture.
    #       32 bit = 'L' and 64 bit = 'I'
    return array.array('I', decoded_data)

def load_actor_layer(map_scene, tag, tile_width, tile_height):
    name = tag.get('name')
    width = int(tag.get('width'))
    height = int(tag.get('height'))
    layer = mapscene.ActorLayer(name)
    for child in tag.findall('object'):
        layer.add_actor(load_actor(map_scene, child, width, height, tile_width, tile_height))
    return layer

def load_actor(map_scene, tag, width, height, tile_width, tile_height):
    # Get object properties
    name = tag.get('name')
    actor_type = tag.get('type')
    x = int(tag.get('x'))
    y = height * tile_height - int(tag.get('y')) - tile_height
    width = int(tag.get('width'))
    height = int(tag.get('height'))
    rect = cocos.rect.Rect(x, y, width, height)
    properties = dict()
    for p in tag.find('properties'):
        properties[p.get('name')] = p.get('value')
    actor = factories[actor_type](properties)
    actor.name = name
    actor.position = (x, y)
    actor.size = (width, height)
    return actor

