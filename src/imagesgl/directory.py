#!/usr/bin/env python3

import json
import os
from imagesgl.entry import Entry

class Directory:
    def __init__(self, basepath):
        self.basepath = basepath
        self.entries = {}
        self.settings = {}
        self.directory_file = None
        self.settings_file = None

    def __repr__(self):
        return "<Directory %s>" % self.basepath

    def get_filtered(self, incl='', excl=''):
        incl = incl.upper()
        excl = excl.upper()
        for k, entry in self.entries.items():
            ok = True
            for f in incl:
                if not f in entry.categories:
                    ok = False
                    break
            for f in excl:
                if f in entry.categories:
                    ok = False
                    break
            if ok: yield k, entry

    def get_filtered_keys(self, incl='', excl=''):
        incl = incl.upper()
        excl = excl.upper()
        for k, entry in self.get_filtered(incl=incl, excl=excl):
            yield k

    def __setitem__(self, key, entry):
        print("Adding %s" % key)
        self.entries[key] = entry

    def __getitem__(self, key):
        return self.entries.get(key)

    def __contains__(self, key):
        return key in self.entries

    def __iter__(self):
        for key, entry in self.entries.items():
            yield entry

    def save(self, filename=None):
        self.directory_file = filename or self.directory_file
        with open(self.directory_file, 'w') as f:
            f.write(json.dumps({k: v.to_dict() for k, v in self.entries.items()}, indent=2))

    def load(self, filename=None):
        self.directory_file = filename or self.directory_file
        with open(self.directory_file, 'r') as f:
            self.entries = {k: Entry(from_dict=v) for k, v in json.load(f).items()}

    def save_settings(self, filename=None):
        self.settings_file = filename or self.settings_file
        with open(self.settings_file, 'w') as f:
            f.write(json.dumps(self.settings, indent=2))

    def load_settings(self, filename=None):
        self.settings_file = filename or self.settings_file
        with open(self.settings_file, 'r') as f:
            self.settings = json.load(f)
            #print(self.settings.get('categories'))

    def delete_all_in_category(self, category):
        deleted = []
        for k, entry in self.get_filtered(incl=category):
            entry.delete_from_disk(self.basepath)
            deleted.append(k)
        for k in deleted:
            del self.entries[k]
        return deleted
