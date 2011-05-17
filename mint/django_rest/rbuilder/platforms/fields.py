#
# Copyright (c) 2011 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#
from django.db import models
from conary import versions


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

        
class CalculatedField(models.Field):
    #TODO : add errors for trying to pass this in.
    pass


class AbstractUrlField(CalculatedField):

    class _Url(models.Model):
        href = CharField()
        value = CharField()
        
        def __repr__(self):
            if self.value:
                return '_Url(%r, value=%r)' % (self.href, self.value)
            else:
                return '_Url(%r)' % (self.href)

    def __repr__(self):
        return 'fields.AbstractUrlField()'

    def getModel(self):
        return self._Url

    def getModelInstance(self, value, parent, context):
        modelClass = self.getModel()
        url = self._getUrl(parent, context)
        if url is None:
            return None
        return modelClass(href=url, value=value)



class AbsoluteUrlField(CalculatedField):
    handleNone = True

    def value_to_string(self, obj):
        pass


class ImageDownloadField(CalculatedField):
    handleNone = True

    def value_to_string(self, obj):
        pass


class EmailField(models.Field):
    pass


class DateTimeField(models.Field):
    pass


class ObjectField(models.Field):
    parser = None
    _emptyIsNone = True

    def to_python(self, value):
        if value is None or (self._emptyIsNone and value == ''):
            return None
        return self.parser(value)

    def value_to_string(self, obj):
        return str(value)


class VersionField(ObjectField):
    parser = staticmethod(versions.VersionFromString)


class LabelField(ObjectField):
    parser = versions.Label


class FlavorField(ObjectField):
    _emptyIsNone = False
    parser = staticmethod(deps.parseFlavor)