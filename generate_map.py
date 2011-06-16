# Generates a map of given dimensions with a border

import sys

if len(sys.argv) != 8:
    print "Usage: %s [width] [height] [tile_size] [tileset] [tile_fill] [tile_border] [outfile]" % sys.argv[0]
    exit(1)

width, height, tile_size, tileset, tile_fill, tile_border, outfile = sys.argv[1:]
width = int(width)
height = int(height)

cell_prefix = "\t\t<cell tile=\""
cell_suffix = "\" />"
rectmap_prefix = "<rectmap id=\""
rectmap_suffix= "\" origin=\"0,0,0\" tile_size=\"%s\">" % tile_size

def make_cell_line(tile):
    return cell_prefix + tile + cell_suffix + "\n"

def make_rectmap_line(id):
    return rectmap_prefix + id + rectmap_suffix + "\n"

f = open(outfile, 'w')

f.write("<resource><requires file=\"%s\" />\n" % tileset)

# Ground layer
f.write(make_rectmap_line("ground"))
for x in range(width):
    f.write("\t<column>\n")
    if x == 0 or x == width - 1:
        for y in range(height):
            f.write(make_cell_line(tile_border))
    else:
        for y in range(height):
            if y == 0 or y == height - 1:
                f.write(make_cell_line(tile_border))
            else:
                f.write(make_cell_line(tile_fill))
    f.write("\t</column>\n")
f.write("</rectmap>\n")

# Fringe layer
f.write(make_rectmap_line("fringe"))
for x in range(width):
    f.write("\t<column>\n")
    for y in range(height):
        f.write(make_cell_line(""))
    f.write("\t</column>\n")
f.write("</rectmap>\n")

# Over layer
f.write(make_rectmap_line("over"))
for x in range(width):
    f.write("\t<column>\n")
    for y in range(height):
        f.write(make_cell_line(""))
    f.write("\t</column>\n")
f.write("</rectmap>\n")

f.write("</resource>\n")
f.close()
     
