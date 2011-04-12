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

from xobj import xobj

class GetSetMixin(object):
    def __get__(self, instance, owner):
        return self._data
        
    def __set__(self, instance, value):
        self._data = self._validate(value)


class XObjInitializer(object):
    def __init__(self, data=None):
        self._data = self._validate(data)

    def __str__(self):
        return str(self._data)
        
    __repr__ = __str__

class CharField(XObjInitializer, GetSetMixin):
    __name__ = 'CharField'

    def _validate(self, value):
        if value:
            assert(isinstance(value, (str, unicode)))
        return value

        
class DecimalField(xobj.XObj):
    __name__ = 'DecimalField'

class FloatField(xobj.XObj):
    __name__ = 'FloatField'

class IntegerField(xobj.XObj):
    __name__ = 'IntegerField'

class TextField(xobj.XObj):
    __name__ = 'TextField'

class ForeignKey(xobj.XObj):
    __name__ = 'ForeignKey'

class ManyToManyField(xobj.XObj):
    __name__ = 'ManyToManyField'

class OneToOneField(xobj.XObj):
    __name__ = 'OneToOneField'

class AutoField(xobj.XObj):
    __name__ = 'AutoField'

class NullBooleanField(xobj.XObj):
    __name__ = 'NullBooleanField'

class DateTimeUtcField(xobj.XObj):
    __name__ = 'DateTimeUtcField'

class SerializedForeignKey(xobj.XObj):
    __name__ = 'SerializedForeignKey'

class HrefField(xobj.XObj):
    __name__ = 'HrefField'

class DeferredForeignKey(xobj.XObj):
    __name__ = 'DeferredForeignKey'

class SmallIntegerField(xobj.XObj):
    __name__ = 'SmallIntegerField'

class XMLField(xobj.XObj):
    __name__ = 'XMLField'

class InlinedDeferredForeignKey(xobj.XObj):
    __name__ = 'InlinedDeferredForeignKey'

class InlinedForeignKey(xobj.XObj):
    __name__ = 'InlinedForeignKey'

class BooleanField(xobj.XObj):
    __name__ = 'BooleanField'

class URLField(xobj.XObj):
    __name__ = 'URLField'

class DateTimeField(xobj.XObj):
    __name__ = 'DateTimeField'
    
class EmailField(xobj.XObj):
    __name__ = 'EmailField'