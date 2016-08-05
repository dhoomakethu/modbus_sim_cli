from __future__ import unicode_literals
from __future__ import absolute_import

import logging
import json
import copy

log = logging.getLogger(__name__)
DEF = object()


class NotANamespace(Exception):
    pass


class Namespace(object):
    """A dot-separated nested namespace which can be built from a dict."""

    def __init__(self, args={}):
        self.update(args)

    def update(self, args):
        if isinstance(args, Namespace) or issubclass(args.__class__,
                                                     Namespace):
            n = args.deepcopy()
            self.__dict__.update(n.to_dict())
            return
        if isinstance(args, dict):
            self.__dict__.update(args)
            for arg in self.__dict__:
                if isinstance(self.__dict__[arg], dict):
                    self.__dict__[arg] = self.__class__(self.__dict__[arg])
        else:
            raise TypeError("Argument 'args' must be a dict. Got: %s" % args)

    def to_dict(self):
        dc = self.__dict__.copy()
        for k in dc:
            if isinstance(dc[k], self.__class__):
                dc[k] = dc[k].to_dict()
        return dc

    def _perform(self, op, obj, part, value=None):
        if isinstance(obj, self.__class__) or issubclass(self.__class__,
                                                         obj.__class__):
            if op == "get":
                return obj.__dict__[part]
            if op == "has":
                if part in obj.__dict__.keys():
                    return True
                else:
                    return False
            if op == "set":
                obj.__dict__[part] = value
                return obj
            if op == "del":
                obj.__dict__.pop(part)
                return obj
        else:
            raise NotANamespace("Not a namespace: %s" % obj)

    def _operation(self, dotstring, default=DEF, value=None, op="get"):
        try:
            dotstring = dotstring.split(".")
            cur_val = self
            if op == "get":
                for part in dotstring:
                    cur_val = self._perform(op, cur_val, part)
                return cur_val
            else:
                if len(dotstring) == 1:
                    part = dotstring[0]
                    if op == "set":
                        cur_val = self._perform(op, cur_val, part, value)
                    elif op == "del":
                        cur_val = self._perform(op, cur_val, part)
                else:
                    tail = dotstring[-1]
                    parts = dotstring[:-1]
                    for part in parts:
                        if self._perform("has", cur_val, part):
                            cur_val = self._perform("get", cur_val, part)
                        else:
                            if op == "set":
                                cur_val = self._perform(
                                    "set", cur_val, part, self.__class__()
                                )
                                cur_val = self._perform("get", cur_val, part)
                    if op == "set":
                        self._perform(op, cur_val, tail, value)
                    elif op == "del":
                        self._perform(op, cur_val, tail)
                return value
        except Exception as e:
            if default is not DEF:
                return default
            else:
                raise e

    def get(self, dotstring, default=DEF):
        return self._operation(dotstring, default=default, op="get")

    def set(self, dotstring, value, default=DEF):
        return self._operation(
            dotstring, value=value, default=default, op="set")

    def remove(self, dotstring, default=DEF):
        return self._operation(dotstring, default=default, op="del")

    def has(self, dotstring):
        try:
            self.get(dotstring)
            return True
        except KeyError:
            return False

    def _str(self, obj):
        return "%s" % obj

    def dump(self):
        return json.dumps(
            self.to_dict(), sort_keys=True, indent=4, default=self._str
        )

    def keys(self):
        return self.__dict__.keys()

    def pprint(self):
        print self.dump()

    def new(self, *args, **kwargs):
        return self.__class__(*args, **kwargs)

    def copy(self):
        return copy.copy(self)

    def deepcopy(self):
        return copy.deepcopy(self)

    def __repr__(self):
        return json.dumps(
            self.to_dict(), indent=4, sort_keys=True, default=repr
        )

    def __setattr__(self, attr, value):
        raise AttributeError("Cannot assign value directly!")

    def __delattr__(self, *args, **kwargs):
        raise AttributeError("Cannot delete value directly!")
