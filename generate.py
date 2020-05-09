#!/usr/bin/env python3

from PIL import Image
from glob import glob
import os

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

letters = read_letters()
for name, ranges in letters.items():
    print("%r: %r" % (name, ranges))


