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
