CocosRPG
========

About
-----
This repo is for my expirements with tile engines in Cocos2D.
The goal is to design a decent codebase that could be used to make an RPG.
This is not a framework. I don't expect this to ever be a library but merely a foundation to write a specific type of game.
That said, I hope that this code could be of use to someone. Particularly, the code that loads Tiled .tmx map files.

Map Files
---------
Map files are in Tiled .tmx format.
Each map file must have tile layers named "ground", "fringe", "over", and "collision" and an object layer named "objects".
Multiple tilesets are supported.
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
No tile = no collision
Any tile = collision
Perhaps this can be improved upon in the future to support many collision types.
### Object layer
Where all game entities such as the player, NPCs, etc. live.
Static objects (things that exist in a map regardless of game state) can be placed in the map file such as Portals and Dialog triggers.
Consult the map files that are included for formatting of these objects.

Try it out!
-----------
### Tile engine test
python rpg.py
### Battle engine test
to be written (I hope...)

License
-------
GPL v3
Because sharing is caring. :)
