#!/usr/bin/env python3

class State:
    def __init__(self, name, mapper={}, alternatives=[], limited=None, optional=False):
        self.name = name
        self.mapper = mapper
        self.alternatives = alternatives
        self.limited = limited if not limited is None else len(self.alternatives) > 0
        self.optional = optional

class Command:
    def __init__(self, name, states={}, starting_state=None, fn=None):
        self.name = name
        self.states = states
        self.starting_state = starting_state
        self.fn = fn
        
    def start(self):
        self.state = self.starting_state

    def give(self, value):
        pass
    

class Interpreter:
    def __init__(self, directory, browser, entry):
        self.directory = directory
        self.browser = browser
        self.entry = entry

        self.commands = {}

    def add(self, command):
        self.commands[command.name] = command
