#!/usr/bin/env python3

from PIL import Image
from glob import glob
import os
import omg

OUTPUT_WORDS = """
U W U
L O L
Acacia
ai
al
Alicia
all
allow
aw
awl
Awol
awooca
cacao
calcic
calculi
calico
call
caw
cilia
claw
Clio
cloaca
coal
coca cola
cocoa
coil
colic
cow
cowl
Cuculi
cull
ill
Io
Iowa
jail
jaw
Jill
Jo
Julia
julio
law
Lila
lilac
lill
local
Lou
Lucia
Lucilia
Lula
lull
Lulu
Ouija
owl
Waco
wail
wall
Wallawalla
wallow
Will
willow
woo
wool
wow
"""

def columns_from_image(filename):
    img = Image.open(filename).convert('RGB')
    w, h = img.size
    result = []
    for x in range(w):
        column = tuple(img.getpixel((x, y)) for y in range(h))
        result.append(column)
    return result

def build_lut(columns):
    result = {}
    for x, column in enumerate(columns):
        result.setdefault(column, []).append(x)
    return result

def fit_to_base(columns, base_lut):
    result = [None] * len(columns)

    # We go through in multiple passes to try to minimize splitting.
    # First, singletons where it's completely unambiguous.
    for x, column in enumerate(columns):
        assert column in base_lut, (
            "Column %d not found in base image!" % x
        )
        candidates = base_lut[column]
        if len(candidates) == 1:
            result[x] = candidates[0]

    while None in result:
        # Next, try to find candidates that match an adjacent column.
        made_progress = False
        for x, column in enumerate(columns):
            candidates = base_lut[column]
            if x > 0 and result[x - 1] is not None:
                left_side = result[x - 1]
                if (left_side + 1) in candidates:
                    result[x] = left_side + 1
                    made_progress = True
                    continue
            if x < len(columns) - 1 and result[x + 1] is not None:
                right_side = result[x + 1]
                if (right_side - 1) in candidates:
                    result[x] = right_side - 1
                    made_progress = True
                    continue

        # If we made no progress in matching adjacents, go through and
        # find a single column that is not yet matched and pick a candidate
        # at random. We re-run the matching afterwards as this may open up
        # new possibilities.
        if not made_progress:
            for x, column in enumerate(columns):
                if result[x] is None:
                    candidates = base_lut[column]
                    result[x] = candidates[0]
                    break

    return result

def make_ranges(column_indexes):
    result = []
    idx = 0
    while idx < len(column_indexes):
        start = column_indexes[idx]
        count = 1
        idx += 1
        while idx < len(column_indexes):
            if column_indexes[idx] != column_indexes[idx - 1] + 1:
                break
            idx += 1
            count += 1
        result.append((start, count))
    return result

def read_letters():
    base = columns_from_image('cyl1_1.gif')
    lut = build_lut(base)

    result = {}
    for filename in glob('letters/*.png'):
        columns = columns_from_image(filename)
        indexes = fit_to_base(columns, lut)
        ranges = make_ranges(indexes)

        name = os.path.basename(filename).replace('.png', '')
        result[name] = ranges

    return result

def make_adder(collection, struct_type):
    def adder(**kwargs):
        result = len(collection)
        collection.append(struct_type(**kwargs))
        return result
    return adder

def make_phrase(s, letters):
    s = s.lower()
    result = []
    for idx, c in enumerate(s):
        if c == ' ':
            letter = letters['long_space']
        else:
            letter = letters[c]
        result.extend(letter)
        if idx + 1 < len(s) and s[idx + 1] != ' ':
            result.extend(letters['short_space'])
    return result

letters = read_letters()

ed = omg.MapEditor()

add_sector = make_adder(ed.sectors, omg.Sector)
add_sidedef = make_adder(ed.sidedefs, omg.Sidedef)
add_linedef = make_adder(ed.linedefs, omg.Linedef)
add_vertex = make_adder(ed.vertexes, omg.Vertex)
add_thing = make_adder(ed.things, omg.Thing)

sec1 = add_sector(z_ceil=96)
sec2 = add_sector(z_ceil=96, z_floor=55)
sd1 = add_sidedef(sector=sec1, tx_mid="STARTAN2")
sd2 = add_sidedef(sector=sec2, tx_mid="SHAWN2")
v1 = add_vertex(x=256, y=13000)
v2 = add_vertex(x=256, y=0)
v3 = add_vertex(x=0, y=0)
v4 = add_vertex(x=0, y=13000)

# Three boring walls
add_linedef(vx_a=v4, vx_b=v1, flags=1, front=sd1)
add_linedef(vx_a=v1, vx_b=v2, flags=1, front=sd1)
add_linedef(vx_a=v2, vx_b=v3, flags=1, front=sd1)

# The fourth wall is built out of small segments:
last_v = v3
y = 0

words = OUTPUT_WORDS.strip().split("\n")
for word in words:
    word = " " + word + " "
    v = add_vertex(x=0, y=y+64)
    add_linedef(vx_a=last_v, vx_b=v, flags=1, front=sd1)
    last_v = v
    y += 64

    start_v = last_v
    backpin_v = add_vertex(x=-1, y=y)

    for offset, npixels in make_phrase(word, letters):
        sd = add_sidedef(sector=sec1, tx_low="SHAWN1", off_x=offset)
        v = add_vertex(x=0, y=y+npixels)
        add_linedef(vx_a=last_v, vx_b=v, front=sd, back=sd2,
                    flags=1+4+16) # impassible, two-sided, lower-unpeg
        last_v = v
        y += npixels

    add_linedef(vx_a=start_v, vx_b=backpin_v, front=sd2, flags=1)
    add_linedef(vx_a=backpin_v, vx_b=last_v, front=sd2, flags=1)

# Tailing end to join back with first linedef
add_linedef(vx_a=last_v, vx_b=v4, front=sd1, flags=1)

# Player 1 start
add_thing(x=128, y=128, type=1, angle=180)

w = omg.WAD()
w.maps["MAP01"] = ed.to_lumps()
w.to_file("letters.wad")

