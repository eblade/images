#!/usr/bin/env python3

import os

class Scanner:
    def __init__(self, basepath, ext=[]):
        self.basepath = basepath
        self.ext = ext

    def scan(self):
        print("Scanning %s..." % self.basepath)
        for r, ds, fs in os.walk(self.basepath):
            for f in fs:
                if not self.ext or f.split('.')[-1].lower() in self.ext:
                    yield os.path.relpath(os.path.join(r, f), self.basepath)
        
