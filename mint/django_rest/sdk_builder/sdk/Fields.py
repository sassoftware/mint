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

# INCLUDED IN CLIENT SIDE DISTRIBUTION #

from rSDK import GetSetMixin, XObjInitializer
from rSDK import ValidationError

class CharField(XObjInitializer, GetSetMixin):
    __name__ = 'CharField'
    
    def _validate(self, value):
        if value and not isinstance(value, (str, unicode)):
            raise ValidationError('Value must be of type str or unicode')
        return value
        
class DecimalField(XObjInitializer, GetSetMixin):
    __name__ = 'DecimalField'
    
    def _validate(self, value):
        return value

class FloatField(XObjInitializer, GetSetMixin):
    __name__ = 'FloatField'
    
    def _validate(self, value):
        return value
        
class IntegerField(XObjInitializer, GetSetMixin):
    __name__ = 'IntegerField'
    
    def _validate(self, value):
        return value

class TextField(XObjInitializer, GetSetMixin):
    __name__ = 'TextField'
    
    def _validate(self, value):
        return value

class ForeignKey(XObjInitializer, GetSetMixin):
    __name__ = 'ForeignKey'
    
    def _validate(self, value):
        return value

class ManyToManyField(XObjInitializer, GetSetMixin):
    __name__ = 'ManyToManyField'
    
    def _validate(self, value):
        return value

class OneToOneField(XObjInitializer, GetSetMixin):
    __name__ = 'OneToOneField'
    
    def _validate(self, value):
        return value

class AutoField(XObjInitializer, GetSetMixin):
    __name__ = 'AutoField'
    
    def _validate(self, value):
        return value

class NullBooleanField(XObjInitializer, GetSetMixin):
    __name__ = 'NullBooleanField'
    
    def _validate(self, value):
        return value

class DateTimeUtcField(XObjInitializer, GetSetMixin):
    __name__ = 'DateTimeUtcField'
    
    def _validate(self, value):
        return value

class SerializedForeignKey(XObjInitializer, GetSetMixin):
    __name__ = 'SerializedForeignKey'
    
    def _validate(self, value):
        return value

class HrefField(XObjInitializer, GetSetMixin):
    __name__ = 'HrefField'
    
    def _validate(self, value):
        return value

class DeferredForeignKey(XObjInitializer, GetSetMixin):
    __name__ = 'DeferredForeignKey'
    
    def _validate(self, value):
        return value

class SmallIntegerField(XObjInitializer, GetSetMixin):
    __name__ = 'SmallIntegerField'
    
    def _validate(self, value):
        return value

class XMLField(XObjInitializer, GetSetMixin):
    __name__ = 'XMLField'
    
    def _validate(self, value):
        return value

class InlinedDeferredForeignKey(XObjInitializer, GetSetMixin):
    __name__ = 'InlinedDeferredForeignKey'
    
    def _validate(self, value):
        return value

class InlinedForeignKey(XObjInitializer, GetSetMixin):
    __name__ = 'InlinedForeignKey'
    
    def _validate(self, value):
        return value

class BooleanField(XObjInitializer, GetSetMixin):
    __name__ = 'BooleanField'
    
    def _validate(self, value):
        return value

class URLField(XObjInitializer, GetSetMixin):
    __name__ = 'URLField'
    
    def _validate(self, value):
        return value

class DateTimeField(XObjInitializer, GetSetMixin):
    __name__ = 'DateTimeField'
    
    def _validate(self, value):
        return value
    
class EmailField(XObjInitializer, GetSetMixin):
    __name__ = 'EmailField'
    
    def _validate(self, value):
        return value