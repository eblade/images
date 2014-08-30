#!/usr/bin/env python3

from imagesgl.command import Param, Command, NeedsEnv, NeedsInterpreter, NeedsBrowser, NeedsDirectory, NeedsEntry, Shortcut, ShortcutSet
from imagesgl.command import MOD_CTRL, MOD_SHIFT, MOD_NONE, LETTER
from imagesgl.browser import Browser, MODE_NORMAL, MODE_THUMBS, MODE_INPUT
import pygame
from pygame.locals import *

import os

def __repr__(): return "<module Browser Commands>"

### Helpers

def create(directory, keys=None):
    b = Browser(directory, MODE_THUMBS)
    b.loader_callback = lambda: pygame.event.post(pygame.event.Event(pygame.USEREVENT, action='loaded'))
    keys = keys if not keys is None else sorted(directory.entries.keys())
    b.use_keys(keys, winsize=pygame.display.get_surface().get_size())
    return b

### Image commands

@Shortcut(MODE_THUMBS, MOD_SHIFT, K_PERIOD,    'rotate_marked', +90)
@Shortcut(MODE_THUMBS, MOD_SHIFT, K_COMMA,     'rotate_marked', -90)
@Shortcut(MODE_THUMBS, MOD_NONE,  K_PAGEUP,    'scroll_up_page')
@Shortcut(MODE_THUMBS, MOD_NONE,  K_PAGEDOWN,  'scroll_down_page')
@Shortcut(MODE_THUMBS, MOD_SHIFT, K_0,         'mark_none')
@Shortcut(MODE_THUMBS, MOD_SHIFT, K_9,         'mark_all')
@Shortcut(MODE_THUMBS, MOD_NONE,  K_SPACE,     'toggle_mark')
@Shortcut(MODE_THUMBS, MOD_SHIFT, K_SPACE,     'mark_from_last')
@Shortcut(MODE_THUMBS, MOD_NONE,  K_UP,        'browser_move', 0, -1)
@Shortcut(MODE_THUMBS, MOD_NONE,  K_DOWN,      'browser_move', 0, +1)
@Shortcut(MODE_THUMBS, MOD_NONE,  K_LEFT,      'browser_move', -1, 0)
@Shortcut(MODE_THUMBS, MOD_NONE,  K_RIGHT,     'browser_move', +1, 0)
@Shortcut(MODE_NORMAL, MOD_NONE,  K_SPACE,     'select', +1)
@Shortcut(MODE_NORMAL, MOD_NONE,  K_BACKSPACE, 'select', -1)
@Shortcut(MODE_THUMBS, MOD_NONE,  K_F3,        'create_thumbnails', False)
@Shortcut(MODE_THUMBS, MOD_NONE,  K_F4,        'filter_directory', 'Most items', '', 'X')
@Shortcut(MODE_THUMBS, MOD_SHIFT, K_F4,        'filter_directory', 'All items', '', '')
@Shortcut(MODE_THUMBS, MOD_CTRL,  tuple(range(K_a, K_z+1)), 'filter_browser', LETTER, LETTER, '')
@Shortcut(MODE_THUMBS, MOD_SHIFT, tuple(range(K_a, K_z+1)), 'toggle_category_marked', LETTER)
class image_shortcuts(ShortcutSet):
    pass

@NeedsDirectory()
@NeedsBrowser()
@Param('angle', int, 0)
class rotate_marked(Command):
    def execute(self, directory, browser, angle):
        for entry in browser.marked:
            entry.rotate(angle)
            entry.create_thumbnail(
                basepath=directory.basepath,
                block_size = browser.block_size,
                border = browser.border,
                override = True
            )

@NeedsBrowser()
class scroll_up_page(Command):
    def execute(self, browser):
        wbw, wbh = browser.get_block_dimensions(pygame.display.get_surface().get_size(), browser.block_size)
        browser.move((0, -wbh))

@NeedsBrowser()
class scroll_down_page(Command):
    def execute(self, browser):
        wbw, wbh = browser.get_block_dimensions(pygame.display.get_surface().get_size(), browser.block_size)
        browser.move((0, +wbh))

@NeedsBrowser()
class mark_none(Command):
    def execute(self, browser):
        browser.mark_none()

@NeedsBrowser()
class mark_all(Command):
    def execute(self, browser):
        browser.mark_all()

@NeedsEntry()
class toggle_mark(Command):
    def execute(self, entry):
        entry.toggle_marked()

@NeedsBrowser()
class mark_from_last(Command):
    def execute(self, browser):
        browser.mark_from_last()

@NeedsBrowser()
@Param('delta', int, 1)
class select(Command):
    def execute(self, browser, delta):
        browser.select(delta, winsize=pygame.display.get_surface().get_size())

@NeedsBrowser()
@Param('x', int, 0)
@Param('y', int, 0)
class browser_move(Command):
    def execute(self, browser, x, y):
        browser.move((x, y), winsize=pygame.display.get_surface().get_size())

@NeedsEnv()
@Param('name', str, 'untitled')
@Param('include', str, '')
@Param('exclude', str, '')
class filter_directory(Command):
    def execute(self, env, name, include, exclude):
        new_browser = create(env.directory, sorted(env.directory.get_filtered_keys(incl=include, excl=exclude)))
        new_browser.name = name
        env.browser = new_browser

@NeedsEnv()
@Param('name', str, 'untitled')
@Param('include', str, '')
@Param('exclude', str, '')
class filter_browser(Command):
    def execute(self, env, name, include, exclude):
        new_browser = create(env.directory, sorted(env.browser.get_filtered_keys(incl=include, excl=exclude)))
        new_browser.name = name
        env.browser = new_browser

@NeedsBrowser()
@Param('override', bool, False)
class create_thumbnails(Command):
    def execute(self, browser, override):
        browser.create_thumbs(override=override)

@NeedsDirectory()
@NeedsBrowser()
@Param('category', str, 0)
class toggle_category_marked(Command):
    def execute(self, directory, browser, category):
        for entry in browser.marked:
            entry.toggle_category(category, directory)

@NeedsBrowser()
@Param('filename', str, 'untitled')
@Param('name', str, 'untitled')
class save_browser(Command):
    def execute(self, browser, filename, name):
        browser.name = name
        browser.save(filename)

@NeedsDirectory()
@NeedsBrowser()
@Param('sub_folder', str, None)
@Param('longest_side', int, 800)
class export_browser_default(Command):
    def execute(self, directory, browser, sub_folder, longest_side):
        sub_folder = browser.name if sub_folder is None else sub_folder
        export_dir = os.path.expanduser(os.path.join(directory.settings.get('export_dir', ''), sub_folder))
        if os.path.exists(export_dir):
            print("PATH EXISTS! Aborting")
            return
        os.mkdir(export_dir)
        name_c = 0
        for entry in browser.entries:
            entry.export(directory.basepath, longest_side, export_dir, "img%.5i.jpg" % name_c)
            name_c += 1

    def list_longest_side(self, interpreter, flt):
        return ['200', '400', '800', '1000', '1200', '1600']
