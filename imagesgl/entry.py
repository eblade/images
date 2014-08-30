#!/usr/bin/env python3

import pygame
import os
import threading
from PIL import Image
from math import pi

IMAGE = 'image'
COLLECTION = 'collection'
NOTE = 'note'

class Entry:
    def __init__(self, filename=None, from_dict=None):
        self.filename = filename
        self.filename_thumb = str(self.filename) + '.thumbnail'
        self.categories = ""
        self.angle = 0
        self.height = 0
        self.width = 0
        self.height_thumb = 0
        self.width_thumb = 0
        self.comment = None
        self.original = None
        self.thumbnail = None
        self.scanned = False
        self.loaded = False
        self.loaded_thumb = False
        self.marked = False
        self.thumb_size = (1, 1) # in blocks
        if filename and filename.endswith('.collection'):
            self.entry_type = COLLECTION
        elif filename and filename.endswith('.note'):
            self.entry_type = NOTE
        else:
            self.entry_type = IMAGE
        self.content = None
        self.name = None
        
        self.scale = 1.0
        self.zoomed = None
        self.x, self.y = 0, 0
        if not from_dict is None:
            #print(from_dict)
            self.from_dict(from_dict)

    def __repr__(self):
        return "<Entry %s>" % self.filename

    def load_thumbnail(self, basepath=None, callback=None):
        thumb_filename = os.path.join(basepath, self.filename_thumb)
        if not os.path.exists(thumb_filename):
            return
        self.thumbnail = pygame.image.load(thumb_filename)
        self.width_thumb, self.height_thumb = self.thumbnail.get_size()
        self.loaded_thumb = True
        if not callback is None:
            callback()

    def create_thumbnail(self, basepath, block_size, border=0, override=False):
        infile = os.path.join(basepath, self.filename)
        outfile = os.path.join(basepath, self.filename_thumb)
        print("Creating thumbnail for", infile)
        if os.path.exists(outfile) and not override:
            print("Thumbnail already exists")
            return
        try:
            im = Image.open(infile)
            with open(outfile, 'w') as out:
                tw, th = self.thumb_size
                w = block_size * tw + border * (tw - 1) * 2 
                h = block_size * th + border * (th - 1) * 2 
                self._resize(im, (w, h), True, out)
                self.load_thumbnail(basepath)
                print("Created thumbnail", outfile)
        except ValueError:
            print("Cannot create thumbnail for '%s' (ValueError)" % infile)
        except OSError:
            print("Cannot create thumbnail for '%s' (OSError)" % infile)
        
    def export(self, basepath, longest_edge, output_dir, output_filename):
        infile = os.path.join(basepath, self.filename)
        print("OUTPUT FILENAME AFTER", output_dir, output_filename)
        outfile = os.path.join(output_dir, output_filename)
        print("Exporting image", infile, "to", outfile)
        try:
            im = Image.open(infile)
            with open(outfile, 'w') as out:
                self.width, self.height = im.size
                if self.width > self.height:
                    scale = float(longest_edge) / float(self.width)
                else:
                    scale = float(longest_edge) / float(self.height)
                w = int(self.width * scale)
                h = int(self.height * scale)
                self._resize(im, (w, h), False, out)
                print("Created image", outfile)
        except ValueError:
            print("Cannot export '%s' -> '%s' (ValueError)" % (infile, outfile))
        except OSError:
            print("Cannot export '%s' -> '%s' (OSError)" % (infile, outfile))

    def to_dict(self):
        return {
            'filename': self.filename,
            'categories': self.categories,
            'angle': self.angle,
            'height': self.height,
            'width': self.width,
            'comment': self.comment,
            'thumb_size': self.thumb_size,
            'type': self.entry_type,
            'name': self.name,
        }

    def from_dict(self, d):
        self.filename = d.get('filename', '')
        self.filename_thumb = self.filename + '.thumbnail'
        self.categories = d.get('categories', "")
        self.angle = d.get('angle', 0)
        self.height = d.get('height', 0)
        self.width = d.get('width', 0)
        self.comment = d.get('comment', None)
        self.thumb_size = d.get('thumb_size', (1, 1))
        self.entry_type = d.get('type', IMAGE)
        self.name = d.get('name', None)

    def load_image(self, basepath=None, callback=None, winsize=None):
        if self.entry_type != IMAGE:
            return
        print("Thread loading", "without callback" if callback is None else "with callback")
        self.original = pygame.image.load(os.path.join(basepath, self.filename))
        self.width, self.height = self.original.get_size()
        self.loaded = True
        if not winsize is None:
            self.zoom_fit(winsize)
        if not callback is None:
            print("Thread Callback")
            callback()
        print("Thread Done")

    def load_image_threaded(self, basepath, callback, winsize=None):
        if self.entry_type != IMAGE:
            return
        print("Loading", "without callback" if callback is None else "with callback")
        t = threading.Thread(target=self.load_image, kwargs={'basepath': basepath, 'callback': callback, 'winsize': winsize})
        t.daemon = True
        t.start()

    def load_thumbnail_threaded(self, basepath, callback):
        t = threading.Thread(target=self.load_thumbnail, kwargs={'basepath': basepath, 'callback': callback})
        t.daemon = True
        t.start()

    def zoom_fit(self, winsize):
        ww, wh = winsize
        self.scale = min(ww / self.width, wh / self.height) if self.angle in (0, 180) else min( ww / self.height, wh / self.width)
        self.zoom(1)
    
    def zoom_0(self):
        self.scale = 1
        self.zoom(1)
    
    def zoom_to(self, scale):
        self.scale = scale 
        self.zoom(1)
    
    def zoom(self, factor):
        self.scale *= factor
        try:
            print("ZOOM: %f %f" % (self.angle, self.scale))
            self.zoomed = pygame.transform.rotozoom(self.original, self.angle, self.scale)
        except pygame.error:
            self.scale /= factor
        except TypeError:
            self.scale /= factor

    @property
    def zoomed_size(self):
        return int(self.width * self.scale),int(self.height * self.scale)

    def position(self, winsize):
        ww, wh = winsize
        iw, ih = self.zoomed_size
        (iw, ih) = (iw, ih) if self.angle in (0, 180) else (ih, iw)
        ny = (wh - ih) / 2 + self.y
        if iw < ww:
            nx = (ww - iw) / 2
        else:
            nx = (ww - iw) / 2 + self.x
            if nx > 0: 
                self.x -= nx
                nx = 0
            if nx + iw < ww: 
                self.x += ww - (nx + iw)
                nx = ww - iw
        if ih < wh:
            ny = (wh - ih) / 2
        else:
            ny = (wh - ih) / 2 + self.y
            if ny > 0: 
                self.y -= ny
                ny = 0
            if ny + ih < wh: 
                self.y += wh - (ny + ih)
                ny = wh - ih
        return nx, ny

    def move(self, delta):
        dx, dy = delta
        self.x -= dx
        self.y -= dy

    def rotate(self, delta):
        self.angle += delta
        if self.angle < 0:
            self.angle = 270
        elif self.angle >= 360:
            self.angle = 0
        self.zoom(1)

    def angle(self, angle):
        self.angle = angle
        self.zoom(1)

    def scan(self, basepath):
        pass
        
    def unload(self):
        del self.original
        self.original = None
        self.zoomed = None
        self.loaded = False

    def toggle_category(self, category, directory=None):
        category = category.upper()
        print("Toggling category '%s'" % category)
        self.categories = ''.join(self.categories)
        print("Original categoriesi '%s'" % self.categories)
        p = self.categories.find(category)
        if p != -1:
            print("Removing category '%s'" % category)
            self.categories = self.categories[:p] + self.categories[p+1:] 
        else:
            print("Adding category '%s'" % category)
            self.categories += category
            if not directory is None:
                catdesc = directory.settings.get('categories', {}).get(category, {})
                rplc = catdesc.get('replace', '')
                for r in rplc:
                    if r in self.categories:
                        self.toggle_category(r)
        self.categories = ''.join(sorted(self.categories))
        print("Resulting categories '%s'" % self.categories)

    def toggle_marked(self):
        self.marked = not self.marked

    def _resize(self, img, box, fit, out):
        '''Downsample the image.
        @param img: Image -  an Image-object
        @param box: tuple(x, y) - the bounding box of the result image
        @param fit: boolean - crop the image to fill the box
        @param out: file-like-object - save the image into the output stream
        '''
        #preresize image with factor 2, 4, 8 and fast algorithm
        factor = 1
        bw, bh = box
        iw = self.width
        ih = self.height
        while (iw*2/factor > 2*bw) and (ih*2/factor > 2*bh):
            factor *=2
        factor /= 2
        if factor > 1:
            img.thumbnail((iw/factor, ih/factor), Image.NEAREST)

        #calculate the cropping box and get the cropped part
        if fit:
            x1 = y1 = 0
            x2, y2 = img.size
            wRatio = 1.0 * x2/box[0]
            hRatio = 1.0 * y2/box[1]
            if hRatio > wRatio:
                y1 = int(y2/2-box[1]*wRatio/2)
                y2 = int(y2/2+box[1]*wRatio/2)
            else:
                x1 = int(x2/2-box[0]*hRatio/2)
                x2 = int(x2/2+box[0]*hRatio/2)
            img = img.crop((x1,y1,x2,y2))

        #Resize the image with best quality algorithm ANTI-ALIAS
        img.thumbnail(box, Image.ANTIALIAS)
        if self.angle:
            img = img.rotate(self.angle)

        #save it into a file-like object
        img.save(out, "JPEG", quality=75)

    def delete_from_disk(self, basepath):
        print("Deleting image %s" % self.filename)
        thumb_filename = os.path.join(basepath, self.filename_thumb)
        filename = os.path.join(basepath, self.filename)
        if os.path.exists(thumb_filename):
            os.remove(thumb_filename)
        if os.path.exists(filename):
            os.remove(filename)
        print("Deleted image %s" % self.filename)
