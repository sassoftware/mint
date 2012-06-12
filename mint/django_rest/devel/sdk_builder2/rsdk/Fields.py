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

from sdk import ValidationError, SDKModel

class CharField(SDKModel):
    __name__ = 'CharField'
    
    @staticmethod
    def _validate(key, value):
        if value and not isinstance(value, (str, unicode)):
            raise ValidationError(
                '%s value is of type %s, but must be of type str or unicode' % (key, type(value)))
        
class DecimalField(SDKModel):
    __name__ = 'DecimalField'
    
    @staticmethod
    def _validate(key, value):
        pass

class FloatField(SDKModel):
    __name__ = 'FloatField'
    
    @staticmethod
    def _validate(key, value):
        pass
        
class IntegerField(SDKModel):
    __name__ = 'IntegerField'
    
    @staticmethod
    def _validate(key, value):
        pass

class TextField(SDKModel):
    __name__ = 'TextField'
    
    @staticmethod
    def _validate(key, value):
        if value and not isinstance(value, (str, unicode)):
            raise ValidationError(
                '%s value is of type %s, but must be of type str or unicode' % (key, type(value)))

class ForeignKey(SDKModel):
    __name__ = 'ForeignKey'
    
    @staticmethod
    def _validate(key, value):
        pass

class ManyToManyField(SDKModel):
    __name__ = 'ManyToManyField'
    
    @staticmethod
    def _validate(key, value):
        pass

class OneToOneField(SDKModel):
    __name__ = 'OneToOneField'
    
    @staticmethod
    def _validate(key, value):
        pass

class AutoField(SDKModel):
    __name__ = 'AutoField'
    
    @staticmethod
    def _validate(key, value):
        pass

class NullBooleanField(SDKModel):
    __name__ = 'NullBooleanField'
    
    @staticmethod
    def _validate(key, value):
        pass

class DateTimeUtcField(SDKModel):
    __name__ = 'DateTimeUtcField'
    
    @staticmethod
    def _validate(key, value):
        pass

class SerializedForeignKey(SDKModel):
    __name__ = 'SerializedForeignKey'
    
    @staticmethod
    def _validate(key, value):
        pass

class HrefField(SDKModel):
    __name__ = 'HrefField'
    
    @staticmethod
    def _validate(key, value):
        pass

class DeferredForeignKey(SDKModel):
    __name__ = 'DeferredForeignKey'
    
    @staticmethod
    def _validate(key, value):
        pass

class SmallIntegerField(SDKModel):
    __name__ = 'SmallIntegerField'
    
    @staticmethod
    def _validate(key, value):
        pass

class XMLField(SDKModel):
    __name__ = 'XMLField'
    
    @staticmethod
    def _validate(key, value):
        pass

class InlinedDeferredForeignKey(SDKModel):
    __name__ = 'InlinedDeferredForeignKey'
    
    @staticmethod
    def _validate(key, value):
        pass

class InlinedForeignKey(SDKModel):
    __name__ = 'InlinedForeignKey'
    
    @staticmethod
    def _validate(key, value):
        pass

class BooleanField(SDKModel):
    __name__ = 'BooleanField'
    
    @staticmethod
    def _validate(key, value):
        pass

class URLField(SDKModel):
    __name__ = 'URLField'
    
    @staticmethod
    def _validate(key, value):
        pass

class DateTimeField(SDKModel):
    __name__ = 'DateTimeField'
    
    @staticmethod
    def _validate(key, value):
        pass
    
class EmailField(SDKModel):
    __name__ = 'EmailField'
    
    @staticmethod
    def _validate(key, value):
        pass