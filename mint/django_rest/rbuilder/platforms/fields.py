#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models


class ProtectedString(str):
    """A string that is not printed in tracebacks"""
    def __safe_str__(self):
        return "<Protected Value>"

    __repr__ = __safe_str__


class IntegerField(models.IntegerField):
    def to_python(self, value):
        if value is None or value == '':
            return None
        return int(value)


class FloatField(models.FloatField):
    def to_python(self, value):
        if value is None or value == '':
            return None
        return float(value)


class CharField(models.CharField):
    def value_to_string(self, obj):
        if isinstance(obj, str):
            return obj.decode('utf8', 'replace')
        else:
            return unicode(obj)


class ProtectedField(CharField):
    def to_python(self, value):
        if value is None or value == '':
            return None
        return ProtectedString(unicode(value))


class BooleanField(models.BooleanField):
    def to_python(self, value):
        if value is None:
            return None
        if isinstance(value, (int, bool)):
            return bool(value)
        value = value.lower()
        if value in ('true', '1'):
            return True
        elif value in ('false', '0', ''):
            return False
        else:
            raise ValueError('Invalid boolean value %r' % (value,))

    def value_to_string(self, obj):
        if obj is None:
            return
        if obj:
            return 'true'
        return 'false'
