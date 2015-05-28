#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from conary import versions
from conary.deps import deps
from conary.lib import util

from mint.rest import modellib
from mint.rest.modellib import Field

import urlparse

class IntegerField(Field):
    def _valueFromString(self, value):
        if value is None or value == '':
            return None
        return int(value)

class FloatField(Field):
    def _valueFromString(self, value):
        if value is None or value == '':
            return None
        return float(value)

class CharField(Field):
    def _valueToString(self, value, parent, context):
        if isinstance(value, str):
            return value.decode('utf8', 'replace')
        else:
            return unicode(value)

class ProtectedField(CharField):
    def _valueFromString(self, value):
        if value is None or value == '':
            return None
        return util.ProtectedString(unicode(value))

class BooleanField(Field):
    def _valueFromString(self, value):
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

    def _valueToString(self, value, parent, context):
        if value is None:
            return
        if value:
            return 'true'
        return 'false'

class CalculatedField(Field):
    #TODO : add errors for trying to pass this in.
    pass

class AbstractUrlField(CalculatedField):

    class _Url(modellib.Model):
        href = CharField(isAttribute=True)
        value = CharField(isText=True)
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


class UrlField(AbstractUrlField):

    def __init__(self, location, urlParameters, *args, **kw):
        query = kw.pop('query', None)
        AbstractUrlField.__init__(self, *args, **kw)
        self.location = location
        if isinstance(urlParameters, str):
            urlParameters = [urlParameters]
        if urlParameters is None:
            urlParameters = []
        self.urlParameters = urlParameters
        self.query = query

    def __repr__(self):
        return 'fields.UrlField()'

    def _getUrl(self, parent, context):
        values = [ getattr(parent, x) for x in self.urlParameters]
        if None in values:
            return None
        values = [str(x) for x in values ]
        href = context.controller.url(context.request, self.location, *values)
        if self.query:
            href += '?' + self.query % parent.__dict__
        return href


class ModelField(Field):

    def __init__(self, model, *args, **kw):
        Field.__init__(self, *args, **kw)
        self.model = model

    def getModel(self):
        return self.model

    def getModelInstance(self, value, parent, context):
        return value
    

class AbsoluteUrlField(CalculatedField):
    handleNone = True
    
    def _valueToString(self, value, parent, context):
        url = parent.get_absolute_url()
        if isinstance(url, basestring):
            # return a path outside restlib
            if not url.startswith("/"):
                raise Exception("absolute URL expected")
            tokens = urlparse.urlsplit(context.request.thisUrl)
            (scheme, netloc, path, query, fragment) = tokens
            return "%s://%s%s" % (scheme, netloc, url)
        else:
            # this is more or less the equivalent of reversing
            # a Django view, except in restlib
            return context.controller.url(context.request, *url)


class ImageDownloadField(CalculatedField):
    handleNone = True

    def _valueToString(self, value, parent, context):
        baseUrl = context.request.baseUrl
        if baseUrl.endswith('api'):
            baseUrl = baseUrl[:-3]
        return baseUrl + 'downloadImage?fileId=%d&urlType=%d' % (
                parent.fileId, parent.urlType)


class EmailField(Field):
    pass

class DateTimeField(Field):
    pass

class ObjectField(Field):
    parser = None
    _emptyIsNone = True

    def _valueFromString(self, value):
        if value is None or (self._emptyIsNone and value == ''):
            return None
        return self.parser(value)

    def _valueToString(self, value, parent, context):
        return str(value)


class VersionField(ObjectField):
    parser = staticmethod(versions.VersionFromString)

class LabelField(ObjectField):
    parser = versions.Label

class FlavorField(ObjectField):
    _emptyIsNone = False
    parser = staticmethod(deps.parseFlavor)


class ListField(Field):
    listType = list
    def __init__(self, modelClass, default=None, *args, **kw):
        self.valueClass = modelClass
        if default is None:
            default = self.listType()
        Field.__init__(self, default=default, *args, **kw)

    def getModel(self):
        # currently can only have lists of models, not lists of
        # any type of field.
        return self.valueClass

    def getModelInstance(self, value, parent, context):
        return value
    
    def isList(self):
        return True


class XObjField(Field):

    def _valueFromString(self, value):
        return value

    def _valueToString(self, value, parent, context):
        return value
