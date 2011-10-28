CocosRPG
========

About
-----
This repo is for my expirements with tile engines in Cocos2D.  The goal is to
design a decent codebase that could be used to make an RPG.  This is not a
framework. I don't expect this to ever be a library but merely a foundation to
write a specific type of game.  That said, I hope that this code could be of
use to someone. Particularly, the code that loads Tiled .tmx map files.

Features
--------
* Multi-layered tile maps
* Integration with the Tiled map editor
* Dynamically populated maps from SQLite database
* Simple XML sprite animation format
* Simple component based map actors

Map Files
---------
Map files are in Tiled .tmx format.  Each map file must have tile layers named
*ground*, *fringe*, *over*, and *collision* and an object layer named
*objects*.  This is a restriction for my particular game, but the tmx loading
code can load any arbitrary layers.  Multiple tilesets are supported.
### Ground layer
The bottom tile layer of the map. Pretty self explanatory.
### Fringe layer
Below the Ground layer but under the Object and Over layer.
Used for overlaying things on the ground.
### Over layer
The top layer.
Used for things that should be drawn over everything else, including objects.
### Collision layer
Defines the collision map.

* No tile = no collision.
* Any tile = collision.

Perhaps this can be improved upon in the future to support many collision
types, but for now it is not a priority.
### Actor layer
Where all actors such as the player, NPCs, etc. live.
Static actors (things that exist in a map regardless of game state) can be
placed in the map file using Tiled's object layer functionality. 
Actors are loaded by calling the appropriate factory method that is registered
at runtime.

SQLite save files
-----------------
All persistent data is stored using SQLite databases. Any type of actor can be
stored in the actor table. Actors consist of properties that are housed in the
actor\_property table. Properties from static actors in .tmx XML files and
dynamic actors from game saves are the same so, consequently, the same factory 
methods can be used to load actors from either source.

Component based actors
----------------------
Actors are merely collections of "component" objects. Components provide a
unique piece of functionality to an actor. Examples are physics, AI, and
graphics. This prevents the issues associated with using deep inheritance
hierarchies to define actor functionality.

Dependencies
------------
* cocos2d
* pyglet

Try it out!
-----------
### Tile engine test
python test.py  
Make sure you are running python 2.7, 3.0 will not work.

License
-------
GPL v3 because sharing is caring. :)
