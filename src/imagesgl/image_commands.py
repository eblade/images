#!/usr/bin/env python3

from imagesgl.command import Param, Command, NeedsInterpreter, NeedsBrowser, NeedsDirectory, NeedsEntry, Shortcut, ShortcutSet
from imagesgl.command import MOD_CTRL, MOD_SHIFT, MOD_NONE, LETTER
from imagesgl.browser import MODE_NORMAL, MODE_THUMBS, MODE_INPUT
from pygame.locals import *

import os

MOVE_SPEED = 50

def __repr__(): return "<module Image Commands>"

### Image commands

@Shortcut((MODE_NORMAL, MODE_THUMBS), MOD_NONE, K_PERIOD, 'rotate', +90)
@Shortcut((MODE_NORMAL, MODE_THUMBS), MOD_NONE, K_COMMA, 'rotate', -90)
@Shortcut(MODE_NORMAL, MOD_NONE, K_PAGEUP, 'zoom', 2)
@Shortcut(MODE_NORMAL, MOD_NONE, K_PAGEDOWN, 'zoom', .5)
@Shortcut(MODE_NORMAL, MOD_NONE, K_0, 'zoom_0')
@Shortcut(MODE_NORMAL, MOD_NONE, K_F1, 'zoom_fit')
@Shortcut(MODE_NORMAL, MOD_NONE, K_UP, 'image_move', 0, -MOVE_SPEED)
@Shortcut(MODE_NORMAL, MOD_NONE, K_DOWN, 'image_move', 0, +MOVE_SPEED)
@Shortcut(MODE_NORMAL, MOD_NONE, K_LEFT, 'image_move', +MOVE_SPEED, 0)
@Shortcut(MODE_NORMAL, MOD_NONE, K_RIGHT, 'image_move', -MOVE_SPEED, 0)
@Shortcut((MODE_NORMAL, MODE_THUMBS), MOD_NONE, K_F9, 'resize_thumbnail', 1, 1)
@Shortcut((MODE_NORMAL, MODE_THUMBS), MOD_NONE, K_F10, 'resize_thumbnail', 2, 2)
@Shortcut((MODE_NORMAL, MODE_THUMBS), MOD_NONE, K_F11, 'resize_thumbnail', 3, 2)
@Shortcut((MODE_NORMAL, MODE_THUMBS), MOD_NONE, K_F12, 'resize_thumbnail', 2, 3)
@Shortcut((MODE_NORMAL, MODE_THUMBS), MOD_NONE, tuple(range(K_a, K_z+1)), 'toggle_category', LETTER)
class image_shortcuts(ShortcutSet):
    pass

@NeedsEntry()
@NeedsDirectory()
@NeedsBrowser()
@Param('angle', int, 0)
class angle(Command):
    def execute(self, entry, directory, browser, angle):
        entry.angle()
        entry.create_thumbnail(
            basepath=directory.basepath,
            block_size = browser.block_size,
            border = browser.border,
            override = True
        )
    
    def list_angle(self, interpreter, flt):
        return ['0', '90', '180', '270']
    
@NeedsEntry()
@NeedsDirectory()
@NeedsBrowser()
@Param('angle', int, 0)
class rotate(Command):
    def execute(self, entry, directory, browser, angle):
        entry.rotate(angle)
        entry.create_thumbnail(
            basepath=directory.basepath,
            block_size = browser.block_size,
            border = browser.border,
            override = True
        )
    
    def list_angle(self, interpreter, flt):
        return ['+90', '-90', '+180', '-180']

@NeedsEntry()
@Param('x', int, 0)
@Param('y', int, 0)
class image_move(Command):
    def execute(self, entry, x, y):
        entry.move((x, y))

@NeedsEntry()
@Param('factor', float, 0.0)
class zoom(Command):
    def execute(self, entry, factor):
        entry.zoom(factor)

@NeedsEntry()
@Param('scale', float, 1.0)
class zoomset(Command):
    def execute(self, entry, scale):
        entry.zoom_to(scale)

@NeedsEntry()
class zoomreset(Command):
    def execute(self, entry):
        entry.zoom_0()

@NeedsEntry()
class zoomfit(Command):
    def execute(self, entry):
        entry.zoom_fit()

@NeedsDirectory()
@NeedsBrowser()
@NeedsEntry()
@Param('override', bool, False)
class create_thumbnail(Command):
    def execute(self, directory, browser, entry, override):
        entry.create_thumbnail(
            basepath=directory.basepath,
            block_size = browser.block_size,
            border = browser.border,
            override = override
        )

    def list_override(self, interpreter, flt):
        return [1, 0]

@NeedsInterpreter()
@NeedsEntry()
@Param('width', int, 1)
@Param('height', int, 1)
class resize_thumbnail(Command):
    def execute(self, interpreter, entry, width, height):
        entry.thumb_size = (width, height)
        interpreter.run('create_thumbnail', True)

    def list_width(self, interpreter, flt):
        return [1, 2, 3, 4]

    def list_height(self, interpreter, flt):
        return [1, 2, 3, 4]

@NeedsDirectory()
@NeedsEntry()
@Param('category', str, 0)
class toggle_category(Command):
    def execute(self, directory, entry, category):
        entry.toggle_category(category, directory)

    def list_category(self, interpreter, flt):
        return [chr(x) for x in range(65, 91)]

@NeedsDirectory()
@NeedsEntry()
@Param('name', str, None)
@Param('longest_side', int, 800)
class export_default(Command):
    def execute(self, directory, entry, name, longest_side):
        export_dir = os.path.expanduser(directory.settings.get('export_dir', ''))
        entry.export(directory.basepath, longest_side, export_dir, name+".jpg")
