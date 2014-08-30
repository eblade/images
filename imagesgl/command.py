#!/usr/bin/env python3

import inspect
from imagesgl.browser import MODE_NORMAL, MODE_THUMBS, MODE_INPUT, MODE_ANY
from imagesgl.inputbox import InputBox, INPUT_OK, INPUT_CANCELLED
from pygame.locals import *

MOD_NONE = 0
MOD_SHIFT = 1
MOD_CTRL = 64
MOD_WTF = 4096

### Decorators

class Param:
    def __init__(self, name, datatype=str, default=None):
        self.name = name
        self.datatype = datatype
        if default is None:
            if datatype is str:
                default = ''
            elif datatype is int:
                default = 0
        self.default = default

    def __call__(self, cls):
        if hasattr(cls, '__params__'):
            cls.__params__ = cls.__params__.copy()
        else:
            cls.__params__ = {}
        cls.__params__[self.name] = self
        return cls
    
    def __repr__(self):
        return "<Param %s>" % self.name

class Needs:
    def __call__(self, cls):
        if hasattr(cls, '__params__'):
            cls.__params__ = cls.__params__.copy()
        else:
            cls.__params__ = {}
        cls.__params__ = cls.__params__.copy()
        cls.__params__[self.name] = self
        return cls

class NeedsEnv(Needs):
    def __init__(self):
        self.name = 'env'

class NeedsInterpreter(Needs):
    def __init__(self):
        self.name = 'interpreter'

class NeedsBrowser(Needs):
    def __init__(self):
        self.name = 'browser'

class NeedsDirectory(Needs):
    def __init__(self):
        self.name = 'directory'

class NeedsEntry(Needs):
    def __init__(self):
        self.name = 'entry'

class Shortcut:
    def __init__(self, mode, mod, key, cmd, *args):
        self.mode = mode if isinstance(mode, (tuple,)) else (mode,)
        self.mod = mod if isinstance(mod, (tuple,)) else (mod,)
        self.key = key if isinstance(key, (tuple,)) else (key,)
        self.cmd = cmd
        self.args = args

    def __repr__(self):
        return "%s(%s)" % (self.cmd, ', '.join([str(a) for a in self.args]))

    def __call__(self, cls):
        if hasattr(cls, '__shortcuts__'):
            cls.__shortcuts__ = cls.__shortcuts__.copy()
        else:
            cls.__shortcuts__ = {}
        for key in self._generate_keys():
            if key in cls.__shortcuts__:
                print("Shortcut key class for", key, "exists")
            else:
                cls.__shortcuts__[key] = self
        return cls
    
    def _generate_keys(self):
        for mode in self.mode:
            for mod in self.mod:
                for key in self.key:
                    yield "%s-%s-%s" % (mode, str(mod), str(key))

class ShortcutSet:
    @property
    def shortcuts(self):
        return self.__shortcuts__ if hasattr(self, '__shortcuts__') else {}

### Classes

class Target:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "<" + self.name + ">"

MODE = Target('mode')
MOD = Target('mod')
KEY = Target('key')
LETTER = Target('letter')

class Command:
    def __init__(self):
        self.name = self.__class__.__name__
        s = inspect.signature(self.execute)
        params = []
        for n in s.parameters:
            params.append(self.__params__.get(n))
        self.__params__ = params
        self.__value_params__ = [p for p in self.__params__ if not issubclass(p.__class__, (Needs,))]

    def __repr__(self):
        return "<Command %s>" % self.name

    def execute(self):
        pass

    def param(self, i):
        if i < len(self.__value_params__):
            return self.__value_params__[i]
        else:
            return None

    @property
    def params(self):
        for param in self.__params__:
            yield param

    @property
    def length(self):
        return len(self.__value_params__)

    def get_alternatives(self, interpreter, param, flt=''):
        c = 'list_'+param
        if hasattr(self, c):
            return getattr(self, c)(interpreter, flt)
        else:
            return []

class Interpreter:
    def __init__(self, env):
        self.env = env
        self.commands = {}
        self.shortcuts = {}
        self.executer = None
        self._mode_stack = []
    
    def __repr__(self):
        return "<Interpreter>"

    def add_command(self, command):
        if command.name == "Command": return
        self.commands[command.name] = command

    def add_shortcuts(self, shortcut_set):
        self.shortcuts.update(shortcut_set.shortcuts)

    def add_module(self, module):
        print("Adding", module.__repr__())
        for cls in [cls for cls in module.__dict__.values() if hasattr(cls, 'execute')]:
            self.add_command(cls())
        for cls in [cls for cls in module.__dict__.values() if hasattr(cls, 'shortcuts')]:
            self.add_shortcuts(cls())

    def run(self, name, *args, **kwargs):
        if not self.executer is None:
            print("Already running a command!")
            return
        cmd = self.commands.get(name, None)
        if cmd is None:
            print("No such command:", name)
            return
        #print("Running command", name, args, kwargs)
        self.push_mode(self.env.browser.mode)
        self.executer = Executer(self, cmd)
        self.executer.push(*args)

    def read_keys(self, mode, mod, keycode, unicode):
        if self.env.browser.mode == MODE_INPUT and self.executer and self.executer.inputbox:
            if keycode == K_ESCAPE:
                self.executer.inputbox.cancel()
            elif keycode == K_RETURN:
                self.executer.inputbox.ok()
            elif keycode == K_BACKSPACE:
                self.executer.inputbox.backspace()
            elif keycode == K_DELETE:
                self.executer.inputbox.delete()
            elif keycode == K_LEFT:
                self.executer.inputbox.move(-1)
            elif keycode == K_RIGHT:
                self.executer.inputbox.move(+1)
            elif keycode == K_UP:
                self.executer.inputbox.select(-1)
            elif keycode == K_DOWN:
                self.executer.inputbox.select(+1)
            elif keycode == K_TAB:
                self.executer.inputbox.auto_complete()
            else:
                self.executer.inputbox.write(unicode)

            self.executer.check_input_box()

        elif self.env.browser.mode != MODE_INPUT:
            for key in self._generate_keys(mode, mod, keycode):
                if key in self.shortcuts:
                    shortcut = self.shortcuts.get(key)
                    self.run(shortcut.cmd, *(self._insert_targets(mode, mod, keycode, shortcut.args)))
                    return
            print("No shortcut found for", mode, mod, key)

    def _generate_keys(self, mode, mod, key):
        if mod >= MOD_WTF: mod -= MOD_WTF
        for m in (mode, MODE_ANY):
            yield "%s-%s-%s" % (m, str(mod), str(key))

    def _insert_targets(self, mode, mod, key, args):
        new_args = []
        for arg in args:
            if arg is MODE:
                new_args.append(mode)
            elif arg is MOD:
                new_args.append(mod)
            elif arg is KEY:
                new_args.append(key)
            elif arg is LETTER:
                new_args.append(chr(key))
            else:
                new_args.append(arg)
        return new_args

    def push_mode(self, mode):
        self._mode_stack.append(mode)

    def pop_mode(self):
        if len(self._mode_stack):
            return self._mode_stack.pop()
        else:
            return MODE_NORMAL

class Executer:
    def __init__(self, interpreter, command, **kwargs):
        self.interpreter = interpreter
        self.command = command
        self.values = kwargs.copy()
        self.param = 0
        self.inputbox = None

    def __repr__(self):
        return "<Executer %s>" % self.command

    def push(self, *args):
        for arg in args:
            param = self.command.param(self.param)
            if param is None:
                print("MISSING PARAM", self.command.__params__)
                continue
            if param.datatype is bool:
                if str(arg) in ('1', 'yes', 'y', 'true', 'True'):
                    self.values[param.name] = True
                else:
                    self.values[param.name] = False
            else:
                try:
                    self.values[param.name] = param.datatype(arg)
                except ValueError:
                    self.values[param.name] = param.default
            self.param += 1

        if self.param >= self.command.length:
            self._finalize()
        else: # Create an InputBox for the coming param
            param = self.command.param(self.param)
            self.inputbox = InputBox()
            self.inputbox.title = param.name
            self.inputbox.prefilled = self.command.get_alternatives(self.interpreter, param.name)
            self.interpreter.env.browser.mode = MODE_INPUT

    def cancel(self):
        self.interpreter.env.browser.mode = self.interpreter.pop_mode()
        self.interpreter.executer = None

    def check_input_box(self):
        if self.inputbox.result == INPUT_OK:
            self.push(self.inputbox.value)
        elif self.inputbox.result == INPUT_CANCELLED:
            self.cancel()
        else:
            param = self.command.param(self.param)
            self.inputbox.prefilled = self.command.get_alternatives(self.interpreter, param.name, flt=self.inputbox.value)
                
    def _finalize(self):
        args = []
        for param in self.command.params:
            if param.__class__ is NeedsEnv:
                args.append(self.interpreter.env)
            elif param.__class__ is NeedsInterpreter:
                args.append(self.interpreter)
            elif param.__class__ is NeedsDirectory:
                args.append(self.interpreter.env.directory)
            elif param.__class__ is NeedsBrowser:
                args.append(self.interpreter.env.browser)
            elif param.__class__ is NeedsEntry:
                if self.interpreter.env.entry is None:
                    print("Command needs entry, but entry is None")
                    self.cancel()
                    return
                args.append(self.interpreter.env.entry)
            elif hasattr(param, 'name'):
                args.append(self.values.get(param.name, None))
            else:
                print("Param", param, "is not compatible")
        print("Executing command", self.command.name, "with arguments", *args)
        self.interpreter.env.browser.mode = self.interpreter.pop_mode()
        self.interpreter.executer = None
        self.command.execute(*args)

    @property
    def value(self):
        param = self.command.param(self.param)
        if param is None:
            print("Error: missing param", self.param)
            return
        if param.name in self.values:
            return self.values.get(param.name)
        else:
            return param.default

