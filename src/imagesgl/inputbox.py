#!/usr/bin/env python3

INPUT_OK = 'ok'
INPUT_CANCELLED = 'cancelled'
INPUT_RESULT = 'result'

class InputBox:
    def __init__(self):
        self.title = ''
        self.value = ''
        self.index = 0
        self.callback_ok = None
        self.callback_cancel = None
        self.result = None

        self.prefilled = []
        self.limited = False
        self.selected = False

        self.result = None

    def __repr__(self):
        return "<InputBox %s>" % self.title
    
    @property
    def display(self):
        return "%s: %s|%s" % (self.title, self.value[:self.index], self.value[self.index:])

    @property
    def selection(self, page_size=10):
        if self.selected is False:
            start = 0
        else:
            start = int(self.selected / page_size) * page_size
        end = start + page_size
        for i, v in enumerate(self.prefilled):
            selected = i is self.selected
            if i >= start and i < end:
                yield v, selected

    def ok(self):
        self.result = INPUT_OK
        if len(self.prefilled) and not self.selected is False:
            self.value = self.prefilled[self.selected]
        if not self.callback_ok is None:
            self.callback_ok(self)

    def cancel(self):
        print("INPUT CANCEL")
        self.result = INPUT_CANCELLED
        if not self.callback_cancel is None:
            self.callback_cancel(self)

    def write(self, char):
        self.value = self.value[:self.index] + char + self.value[self.index:]
        self.index += 1
        self.selected = False
        print("Did write")

    def move(self, delta):
        if delta == 1 and self.index == len(self.value):
            self.auto_complete()
        else:
            self.index += delta
            self.index = max(0, self.index)
            self.index = min(len(self.value), self.index)

    def select(self, delta):
        if self.selected is False:
            if len(self.prefilled):
                self.selected = 0
        else:
            self.selected += delta
            self.selected = max(0, self.selected)
            self.selected = min(len(self.prefilled) - 1, self.selected)
        print("Selected is %s" % str(self.selected)) 

    def backspace(self):
        if self.index == 0 or len(self.value) == 0:
            return
        self.value = self.value[:self.index-1] + self.value[self.index:]
        self.index -= 1
        self.selected = False
        print("Did backspace")
        
    def delete(self):
        if self.index >= len(self.value) or len(self.value) == 0:
            return
        self.value = self.value[:self.index] + self.value[self.index+1:]
        self.selected = False
        print("Did delete")
    
    def auto_complete(self):
        if not self.selected is False:
            self.value = str(self.prefilled[self.selected])
        elif len(self.prefilled):
            self.value = str(self.prefilled[0])
        self.index = len(self.value)
