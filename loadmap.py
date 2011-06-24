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

class TileSet(list):
    pass

class AnimSet(dict):
    pass

class MapException(Exception):
    pass

class Map(cocos.layer.ScrollingManager, dict):
    factories = dict()
    @classmethod
    def register_object_factory(cls, name):
        def decorate(func):
            cls.factories[name] = func
            return func
        return decorate

    def __init__(self, filename, db):
        cocos.layer.ScrollingManager.__init__(self)
        dict.__init__(self)
        self.db = db
        self.load(filename)

    def clear_layers(self):
        # Remove layers from scroller if this isn't the first time this map is being loaded
        if len(self.children):
            self.remove('ground')
            self.remove('fringe')
            self.remove('over')
            self.remove('objects')

    def add_layers(self):
        # Add new layers to scrolling layer
        self.add(self['ground'], z=0, name='ground')
        self.add(self['fringe'], z=1, name='fringe')
        self.add(self['objects'], z=2, name='objects')
        self.add(self['over'], z=3, name='over')

    def load(self, filename):
        self.filename = filename
        tree = ElementTree.parse(filename)
        root = tree.getroot()

        # Root level tag is expected to be <map> so raise an exception if it's not
        if root.tag != 'map':
            raise MapException('%s root level tag is %s rather than <map>' % (filename, root.tag))
        # We can only orthogonal maps here because that's all I care about
        if root.get('orientation') != 'orthogonal':
            raise MapException('Map orientation %s not supported. Orthogonal maps only' % root.get('orientation'))

        # Get map properties
        self.width = int(root.get('width'))
        self.height = int(root.get('height'))
        self.tile_width = int(root.get('tilewidth'))
        self.tile_height = int(root.get('tileheight'))

        # Load tilesets
        self.tileset = TileSet()
        for tag in root.findall('tileset'):
            self.tileset += self.load_tileset(tag)

        self.clear_layers()

        # Load layers
        for tag in root.findall('layer'):
            layer = self.load_layer(tag)
            self[layer.id] = layer
        # Load object layers
        for tag in root.findall('objectgroup'):
            layer = self.load_object_layer(tag)
            self[layer.id] = layer
        # Load objects form database
        self.load_from_db()

        self.add_layers()

    def load_from_db(self):
        import entity
        # Get mapnum associated with this map file
        c = self.db.cursor()
        args = (self.filename,)
        c.execute('SELECT mapnum FROM map WHERE file=?', args)
        mapnum = c.fetchone()[0]
        # Get all npc rows
        args = (mapnum,)
        c.execute('SELECT name, file, x, y, dialog FROM npc WHERE mapnum=?', args)
        animsets = dict()
        for row in c:
            # Give the rows descriptive names
            npc_name, npc_anim_file, npc_x, npc_y, npc_dialog = row
            npc_x, npc_y = int(npc_x), int(npc_y)
            # Load animset
            tag = ElementTree.parse(npc_anim_file).getroot()
            if tag.tag != 'animset':
                raise MapException('Expected <animset> tag, found <%s> tag' % tag.tag)
            if npc_anim_file not in animsets:
                animset = self.load_animset(tag)
                animsets[npc_anim_file] = animset
            # Create character
            npc = entity.Character(npc_name, animsets[npc_anim_file], cocos.rect.Rect(0, 0, 24, 24), (0,0), 300, dialog=npc_dialog)
            npc.position = npc_x, npc_y
            self['objects'].add_object(npc)

    def load_animset(self, tag):
        # Get animset properties
        image = pyglet.resource.image(tag.get('image'))
        tile_width = int(tag.get('tilewidth'))
        tile_height = int(tag.get('tileheight'))
        # Create image sequence of tiles
        grid = pyglet.image.ImageGrid(image, image.width / tile_width, image.height / tile_height)
        sequence = grid.get_texture_sequence()
        anims = AnimSet()
        # Loop through all animations
        for child in tag.findall('anim'):
            anim_name = child.get('name')
            anim_duration = float(child.get('duration'))
            frame_indices = [int(x) for x in child.text.split(',')]
            frames = list()
            for f in frame_indices:
                frames.append(sequence[f])
            anims[anim_name] = pyglet.image.Animation.from_image_sequence(frames, anim_duration, loop=True)
        return anims

    def load_tileset(self, tag):
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
        image, image_width, image_height  = self.load_image(child)

        # Construct tileset
        #tileset = cocos.tiles.TileSet(name, None)
        tileset = TileSet()
        for y in range(0, image_height, tile_height):
            for x in range(0, image_width, tile_width):
                tile = image.get_region(x, image_height - y - tile_height, tile_width, tile_height)
                tileset.append(cocos.tiles.Tile(y * (image_width / tile_width) + x, None, tile))
                # set texture clamping to avoid mis-rendering subpixel edges
                # Taken from cocos2d tiles.py
                # BSD licensed
                tile.texture.id
                glBindTexture(tile.texture.target, tile.texture.id)
                glTexParameteri(tile.texture.target, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                glTexParameteri(tile.texture.target, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        return tileset

    def load_image(self, tag):
        # Get image properties
        source = tag.get('source')
        width = int(tag.get('width'))
        height = int(tag.get('height'))

        return pyglet.resource.image(source), width, height

    def load_layer(self, tag):
        # Get layer properties
        name = tag.get('name')
        width = int(tag.get('width'))
        height = int(tag.get('height'))

        child = tag.find('data')
        # Raise exception if there is no <data> tag because that's fucked up
        if child == None:
            raise MapException('No <data> tag in layer')
        # Load layer data
        data = self.load_data(child)
        # Construct layer
        columns = []
        for i in range(0, width):
            row = []
            columns.append(row)
            for j in range(0, height):
                index = j * width + i
                tile = self.tileset[data[index] - 1]
                if data[index] == 0:
                    tile = None
                row.insert(0, cocos.tiles.RectCell(i, height - j - 1, self.tile_width, self.tile_height, None, tile))
        return cocos.tiles.RectMapLayer(name, self.tile_width, self.tile_height, columns, (0,0,0), None)

    def load_data(self, tag):
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

    def load_object_layer(self, tag):
        import entity
        name = tag.get('name')
        width = int(tag.get('width'))
        height = int(tag.get('height'))
        layer = entity.ObjectLayer(name)
        for child in tag.findall('object'):
            layer.add_object(self.load_object(child))
        return layer

    def load_object(self, tag):
        # Get object properties
        name = tag.get('name')
        type = tag.get('type')
        x = int(tag.get('x'))
        y = self.height * self.tile_height - int(tag.get('y')) - self.tile_height
        width = int(tag.get('width'))
        height = int(tag.get('height'))
        rect = cocos.rect.Rect(x, y, width, height)
        properties = dict()
        for p in tag.find('properties'):
            properties[p.get('name')] = p.get('value')
        return self.factories[type](self, name, rect, properties)

