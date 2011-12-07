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

from sdk import XObjInitializer, ValidationError

class CharField(XObjInitializer):
    __name__ = 'CharField'
    
    @staticmethod
    def _validate(key, value):
        if value and not isinstance(value, (str, unicode)):
            raise ValidationError(
                '%s value is of type %s, but must be of type str or unicode' % (key, type(value)))
        return value
        
class DecimalField(XObjInitializer):
    __name__ = 'DecimalField'
    
    @staticmethod
    def _validate(key, value):
        return value

class FloatField(XObjInitializer):
    __name__ = 'FloatField'
    
    @staticmethod
    def _validate(key, value):
        return value
        
class IntegerField(XObjInitializer):
    __name__ = 'IntegerField'
    
    @staticmethod
    def _validate(key, value):
        return value

class TextField(XObjInitializer):
    __name__ = 'TextField'
    
    @staticmethod
    def _validate(key, value):
        if value and not isinstance(value, (str, unicode)):
            raise ValidationError(
                '%s value is of type %s, but must be of type str or unicode' % (key, type(value)))
        return value

class ForeignKey(XObjInitializer):
    __name__ = 'ForeignKey'
    
    @staticmethod
    def _validate(key, value):
        return value

class ManyToManyField(XObjInitializer):
    __name__ = 'ManyToManyField'
    
    @staticmethod
    def _validate(key, value):
        return value

class OneToOneField(XObjInitializer):
    __name__ = 'OneToOneField'
    
    @staticmethod
    def _validate(key, value):
        return value

class AutoField(XObjInitializer):
    __name__ = 'AutoField'
    
    @staticmethod
    def _validate(key, value):
        return value

class NullBooleanField(XObjInitializer):
    __name__ = 'NullBooleanField'
    
    @staticmethod
    def _validate(key, value):
        return value

class DateTimeUtcField(XObjInitializer):
    __name__ = 'DateTimeUtcField'
    
    @staticmethod
    def _validate(key, value):
        return value

class SerializedForeignKey(XObjInitializer):
    __name__ = 'SerializedForeignKey'
    
    @staticmethod
    def _validate(key, value):
        return value

class HrefField(XObjInitializer):
    __name__ = 'HrefField'
    
    @staticmethod
    def _validate(key, value):
        return value

class DeferredForeignKey(XObjInitializer):
    __name__ = 'DeferredForeignKey'
    
    @staticmethod
    def _validate(key, value):
        return value

class SmallIntegerField(XObjInitializer):
    __name__ = 'SmallIntegerField'
    
    @staticmethod
    def _validate(key, value):
        return value

class XMLField(XObjInitializer):
    __name__ = 'XMLField'
    
    @staticmethod
    def _validate(key, value):
        return value

class InlinedDeferredForeignKey(XObjInitializer):
    __name__ = 'InlinedDeferredForeignKey'
    
    @staticmethod
    def _validate(key, value):
        return value

class InlinedForeignKey(XObjInitializer):
    __name__ = 'InlinedForeignKey'
    
    @staticmethod
    def _validate(key, value):
        return value

class BooleanField(XObjInitializer):
    __name__ = 'BooleanField'
    
    @staticmethod
    def _validate(key, value):
        return value

class URLField(XObjInitializer):
    __name__ = 'URLField'
    
    @staticmethod
    def _validate(key, value):
        return value

class DateTimeField(XObjInitializer):
    __name__ = 'DateTimeField'
    
    @staticmethod
    def _validate(key, value):
        return value
    
class EmailField(XObjInitializer):
    __name__ = 'EmailField'
    
    @staticmethod
    def _validate(key, value):
        return value