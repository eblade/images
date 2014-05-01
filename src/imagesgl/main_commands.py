#!/usr/bin/env python3

import sys
from imagesgl.command import Param, Command, NeedsInterpreter, NeedsBrowser, NeedsDirectory, NeedsEntry, NeedsEnv, Shortcut, ShortcutSet
from imagesgl.command import MOD_CTRL, MOD_SHIFT, MOD_NONE
from imagesgl.browser import MODE_NORMAL, MODE_THUMBS, MODE_INPUT, MODE_ANY
import pygame
from pygame.locals import *

def __repr__(): return "<module Main Commands>"

### Main commands

@Shortcut(MODE_THUMBS, MOD_NONE, K_ESCAPE, 'quit')
@Shortcut(MODE_NORMAL, MOD_NONE, K_ESCAPE, 'toggle_view')
@Shortcut((MODE_THUMBS, MODE_NORMAL), MOD_NONE, K_RETURN, 'toggle_view')
@Shortcut((MODE_THUMBS, MODE_NORMAL), MOD_NONE, K_F5, 'toggle_fullscreen')
@Shortcut((MODE_THUMBS, MODE_NORMAL), MOD_NONE, K_F1, 'command_mode')
@Shortcut((MODE_THUMBS, MODE_NORMAL), MOD_NONE, K_F2, 'toggle_info')
@Shortcut((MODE_THUMBS, MODE_NORMAL), MOD_SHIFT, K_SEMICOLON, 'command_mode')
class image_shortcuts(ShortcutSet):
    pass

@NeedsDirectory()
class quit(Command):
    def execute(self, directory):
        directory.save()
        directory.save_settings()
        pygame.display.quit()
        sys.exit(0)

@NeedsBrowser()
@NeedsEnv()
class toggle_view(Command):
    def execute(self, browser, env):
        if browser.mode == MODE_THUMBS:
            browser.mode = MODE_NORMAL
            browser.load_neighborhood(winsize=env.winsize)
        elif browser.mode == MODE_NORMAL:
            browser.mode = MODE_THUMBS

class toggle_fullscreen(Command):
    def execute(self):
        # should set fullscreen resolution here
        pygame.display.toggle_fullscreen()

@NeedsBrowser()
class toggle_view(Command):
    def execute(self, browser):
        browser.show_info = not browser.show_info

@NeedsInterpreter()
@Param('command', str, 'help')
class command_mode(Command):
    def execute(self, interpreter, command):
        print("COMMAND MODE")
        interpreter.run(command)

    def list_command(self, interpreter, flt):
        return sorted([c for c in interpreter.commands.keys() if flt in c])

@NeedsDirectory()
@Param('key', str, None)
@Param('value', str, None)
class setting(Command):
    def execute(self, directory, key, value):
        old_value = directory.settings.get(key, None)
        if isinstance(old_value, (list, )):
            value = ','.split(value) # Check this!
        directory.settings[key] = value

    def list_key(self, interpreter, flt):
        return sorted([c for c in interpreter.env.directory.settings.keys() if flt in c])
