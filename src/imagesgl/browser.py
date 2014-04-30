#!/usr/bin/env python3

import math
import threading
import os.path
import json

# Browser modes
MODE_NORMAL = 'normal'
MODE_THUMBS = 'thumbs'
MODE_INPUT = 'input'
MODE_ANY = '*'

class Browser:
    def __init__(self, directory, mode):
        self.mode = mode
        self.directory = directory
        self.entries = []
        self.selected_index = 0
        self.selected_image = None
        self.loader_callback = None
        self.block_size = 200
        self.border = 5
        self.name = "Unititled collection"

        self.thumb_start_row = 0
        self.thumb_scroll_target = 0
        self.thumb_map = []
        self.thumb_pos = []
        self.distributed = False
        
        self.filename = None

    def __repr__(self):
        return "<Browser %s>" % self.name

    def save(self, filename=None):
        filepath = (filename or self.filename)
        if not filepath.endswith(".collection"): filepath += ".collection"
        filepath = os.path.join(self.directory.basepath, filepath)
        print("Saving collection as", filepath)
        with open(filepath, 'w') as f:
            f.write(json.dumps({"name": self.name, "entries": list(self.get_filtered_keys(''))}, indent=2))

    def load(self, filename):
        filepath = os.path.join(self.directory.basepath, filename)
        print("Loading collection", filepath)
        with open(filepath, 'r') as f:
            self.filename = filename
            data = json.load(f)
            self.name = data.get('name', self.name)
            self.use_keys(data.get('entries', []))

    @property
    def title_msg(self):
        return "%s - %i items" % (self.name, len(self.entries))

    def get_filtered(self, incl='', excl=''):
        incl = incl.upper()
        excl = excl.upper()
        for entry in self.entries:
            ok = True
            for f in incl:
                if not f in entry.categories:
                    ok = False
                    break
            for f in excl:
                if f in entry.categories:
                    ok = False
                    break
            if ok: yield entry

    def get_filtered_keys(self, incl='', excl=''):
        incl = incl.upper()
        excl = excl.upper()
        for entry in self.get_filtered(incl=incl, excl=excl):
            yield entry.filename

    def get_marked_keys(self):
        for image in self.entries:
            if image.marked: yield image.filename
    
    @property
    def marked(self):
        for image in self.entries:
            if image.marked: yield image

    def mark_none(self):
        for image in self.entries:
            image.marked = False

    def mark_all(self):
        for image in self.entries:
            image.marked = True

    def mark_from_last(self):
        for image in reversed(self.entries[:self.selected_index+1]):
            if image.marked:
                return
            image.marked = True

    def use_keys(self, keys, winsize=None):
        self.distributed = False
        self.entries = [self.directory[key] for key in keys if key in self.directory]
        self.selected_index = 0
        self.select(0, winsize=winsize)

    def select(self, delta, winsize=None):
        if len(self.entries) == 0:
            return
        # Stepping with wrapping
        self.selected_index += delta
        if self.selected_index < 0:
            self.selected_index = len(self.entries) - 1
        elif self.selected_index >= len(self.entries):
            self.selected_index = 0

        #print("Selecting", self.selected_index)
        self.selected_image = self.entries[self.selected_index]
        if self.mode == MODE_NORMAL:
            self.load_neighborhood(winsize=winsize)

    def goto(self, i, winsize=None):
        if len(self.entries) == 0:
            return
        self.selected_index = len(self.entries) - 1 if i is None else i
        #print("Going to", self.selected_index)
        self.select(0, winsize=winsize)

    def move(self, d, winsize=None):
        if len(self.entries) == 0:
            return
        dx, dy = d
        wbw, wbh = len(self.thumb_map[0]), len(self.thumb_map)
        x, y = self.thumb_pos[self.selected_index]
        #print((dx, dy), (wbw, wbh), (x, y))
        while self.thumb_map[y][x] == self.selected_index:
            x += dx
            y += dy
            if x < 0:
                x = wbw - 1
                y -= 1
            elif x >= wbw:
                x = 0
                y += 1
            if y < 0:
                y = wbh - 1
            elif y >= wbh:
                y = 0
        self.goto(self.thumb_map[y][x], winsize)
        
        
    def load_neighborhood(self, winsize=None):
        c = self.selected_index
        n = self.selected_index + 1 if ((self.selected_index + 2) <= len(self.entries)) else 0
        p = self.selected_index - 1 if self.selected_index > 0 else len(self.entries) - 1
        for i, image in enumerate(self.entries):
            if not i in (c, n, p):
                image.unload()
        for i in (c, n, p): 
            image = self.entries[i]
            if not image.loaded:
                image.load_image_threaded(
                    basepath=self.directory.basepath, 
                    callback=self.loader_callback if i==c else None,
                    winsize=winsize
                )
            elif i == c:
                self.loader_callback()

    def unload(self):
        for i, image in enumerate(self.entries):
            image.unload()
            image.unload_thumbnail()

    def load_thumbs(self):
        for i, image in enumerate(self.entries):
            image.load_thumbnail(self.directory.basepath, callback=self.loader_callback)

    def create_thumbs(self, override=False):
        for i, image in enumerate(self.entries):
            image.create_thumbnail(self.directory.basepath, border=self.border, block_size=self.block_size, override=override)

    def get_block_dimensions(self, winsize, block_size):
        ww, wh = winsize
        return int(float(ww)/block_size), int(float(wh)/block_size)

    def _get_first_free(self, m, i, size):
        if len(m) == 0:
            return -1, -1
        ow, oh = len(m[0]), len(m)
        iw, ih = size
        for y in range(oh - ih + 1):
            for x in range(ow - iw + 1):
                if m[y][x] is None:
                    for ix in range(iw):
                        for iy in range(ih):
                            #print("Setting:", x+ix, y+iy) 
                            m[y+iy][x+ix] = i
                    return x, y
        return -1, -1

    def _distribute(self, wbw, wbh):
        if self.distributed:
            return
        print(" * Redistributing * ")
        self.thumb_map = []
        self.thumb_pos = [None for x in range(len(self.entries))]
        for i, image in enumerate(self.entries):
            bw, bh = image.thumb_size
            #print((ww, wh), (wbw, wbh), (bw, bh))
            (x, y) = (-1, -1)
            while (x, y) == (-1, -1):
                x, y = self._get_first_free(self.thumb_map, i, (bw, bh))
                self.thumb_pos[i] = (x, y)
                if (x, y) == (-1, -1):
                    self.thumb_map.append([None for x in range(wbw)])
        #for r in self.thumb_map:
        #    print(' '.join(["%4s" % str(c) for c in r]))
        self.distributed = True
        
    def _ensure_selected_visible(self, wbh):
        i, (w, h) = self.selected_index, self.selected_image.thumb_size
        x, y = self.thumb_pos[i]
        if y == 0:
            #print("Setting start row to 0")
            self.thumb_start_row = 0 
            return
        h = min(h, wbh)
        first = max(y - wbh + h, 0)
        last = max(y, first)
        #print("I is", i, "y is" , y, "h is", h, "wbh is", wbh, "First is", first, "last is", last, "start is", self.thumb_start_row)
        if self.thumb_start_row < first:
            #print("Setting start row to first", first)
            self.thumb_start_row = first 
        elif self.thumb_start_row > last:
            #print("Setting start row to last", last)
            self.thumb_start_row = last 
        else:
            #print("Keeping start row at ", self.thumb_start_row)
            pass
        
    def _is_visible(self, y, wbh, image):
        w, h = image.thumb_size
        first = self.thumb_start_row - h + 1
        last = self.thumb_start_row + wbh
        return y >= first and y <= last

    def thumbs(self, winsize):
        if len(self.entries) == 0:
            return
        ww, wh = winsize
        with_border = self.block_size + self.border * 2
        wbw, wbh = self.get_block_dimensions(winsize, with_border)
        self._distribute(wbw, wbh)
        self._ensure_selected_visible(wbh)
        left_margin = (ww - wbw * with_border) / 2
        top_margin = 35
        min_height = 0
        start_row = max(0, self.thumb_start_row - 2)
        end_row = min(len(self.thumb_map), self.thumb_start_row + wbh + 1)
        drawn = []
        for y_, row in enumerate(self.thumb_map[start_row:end_row]):
            y = start_row + y_
            for x, i in enumerate(row):
                if i is None or i in drawn:
                    continue
                drawn.append(i)
                image = self.entries[i]
                if self._is_visible(y, wbh, image): 
                    x_pos = x * with_border + left_margin
                    y_pos = (y - self.thumb_start_row) * with_border + top_margin
                    if not image.loaded_thumb:
                        image.load_thumbnail_threaded(self.directory.basepath, callback=self.loader_callback)
                    yield image, x_pos, y_pos, image == self.selected_image
