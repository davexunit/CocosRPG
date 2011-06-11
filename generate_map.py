# Generates a map of given dimensions with a border

import sys

if len(sys.argv) != 9:
    print "Usage: %s [name] [width] [height] [tile_size] [tileset] [tile_fill] [tile_border] [outfile]" % sys.argv[0]
    exit(1)

name, width, height, tile_size, tileset, tile_fill, tile_border, outfile = sys.argv[1:]
width = int(width)
height = int(height)

f = open(outfile, 'w')

f.write("<resource><requires file=\"%s\" />\n" % tileset)
f.write("<rectmap id=\"%s\" origin=\"0,0,0\" tile_size=\"%s\">\n" % (name, tile_size))

for x in range(width):
    f.write("<column>\n")
    if x == 0 or x == width - 1:
        for y in range(height):
            f.write("<cell tile=\"%s\" />\n" % tile_border)
    else:
        for y in range(height):
            if y == 0 or y == height - 1:
                f.write("<cell tile=\"%s\" />\n" % tile_border)
            else:
                f.write("<cell tile=\"%s\" />\n" % tile_fill)

    f.write("</column>\n")

f.write("</rectmap>\n")
f.write("</resource>\n")
f.close()
     
