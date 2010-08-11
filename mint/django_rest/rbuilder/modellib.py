#!/usr/bin/python

import datetime
from dateutil import tz
import urlparse

from django.db import models
from django.db.models.fields import related
from django.core import exceptions
from django.core import urlresolvers 

from xobj import xobj

type_map = {}

class BaseManager(models.Manager):
    _transient = True

    def load(self, model_inst):
        try:
            loaded_model = self.get(**model_inst.load_fields_dict())
        except exceptions.ObjectDoesNotExist:
            loaded_model = None
        if loaded_model:
            for field in loaded_model._meta.fields:
                try:
                    if getattr(model_inst, field.name) is None:
                        continue
                except exceptions.ObjectDoesNotExist:
                    continue
                if getattr(model_inst, field.name) != \
                   getattr(loaded_model, field.name):
                    setattr(loaded_model, field.name, 
                        getattr(model_inst, field.name))
            loaded_model._to_set = getattr(model_inst, '_to_set', {})
            return loaded_model
        else:
            return None

    def load_from_href(self, obj, request):
        href = getattr(obj, 'href', None)
        if href:
            path = urlparse.urlparse(href).path
            resolver = urlresolvers.resolve(path)
            func, args = resolver[0:2]
            model = func.get(*args)
            return model
        else:
            return None

    def load_from_object(self, obj, request, save=True):
        model = self.model()
        fields = {}
        for f in model._meta.fields:
            fields[f.name] = f
        accessors = {}
        for r in model._meta.get_all_related_objects():
            accessors[r.get_accessor_name()] = r
        for key, val in obj.__dict__.items():
            if key in fields.keys():
                if isinstance(fields[key], related.RelatedField):
                    val = fields[key].related.parent_model.objects.load_from_href(val, request)
                elif val:
                    val = str(val)
                else:
                    val = None
                setattr(model, key, val)

        loaded_model = self.load(model)
        if not loaded_model:
            if save:
                model.save()
            loaded_model = model
        for key, val in obj.__dict__.items():
            if key in accessors.keys():
                rel_obj_name = accessors[key].var_name
                rel_objs = getattr(val, rel_obj_name, None)
                if rel_objs is None:
                    continue
                if type(rel_objs) != type([]):
                    rel_objs = [rel_objs]
                for rel_obj in rel_objs:
                    rel_mod = type_map[rel_obj_name].objects.load_from_object(
                        rel_obj, request, save=False)
                    getattr(loaded_model, key).add(rel_mod)
        return loaded_model
    
class XObjModel(models.Model):
    objects = BaseManager()

    class Meta:
        abstract = True

    list_fields = []
    load_fields = {}

    def load_fields_dict(self):
        fields_dict = {}
        for f in self.load_fields:
            fields_dict[f.name] = getattr(self, f.name, None)
        return fields_dict

    def to_xml(self, request=None):
        xobj_model = self.serialize(request)
        return xobj.toxml(xobj_model, xobj_model.__class__.__name__)

    def get_absolute_url(self, request=None, pk=None):
        view_name = getattr(self, 'view_name', self.__class__.__name__)
        if not pk:
            url_key = getattr(self, 'pk', [])
        else:
            url_key = pk
        if url_key:
            url_key = [str(url_key)]
        bits = (view_name, url_key)
        try:
            relative_url = urlresolvers.reverse(bits[0], None, *bits[1:3])
        except urlresolvers.NoReverseMatch:
            return None
        if request:
            return request.build_absolute_uri(relative_url)
        else:
            return relative_url

    def _serialize_hrefs(self, request=None):
        href_fields = [(f, v) for f, v in self.__class__.__dict__.items() \
                        if isinstance(v, XObjHrefModel)]
        for href in href_fields:
            href[1].serialize(request)

    def serialize(self, request=None):
        self._serialize_hrefs(request)
        name = self.__class__.__name__
        name = name[0].lower() + name[1:]
        xobj_model = type(name, (object,), {})()

        fields = {}
        for f in self._meta.fields:
            fields[f.name] = f
        accessors = {}
        for r in self._meta.get_all_related_objects():
            accessors[r.get_accessor_name()] = r

        for key, val in self.__dict__.items():
            if key in fields.keys():
                if val is None:
                        val = ''
                elif isinstance(fields[key], models.DateTimeField):
                    val = val.replace(tzinfo=tz.tzutc())
                    val = val.isoformat()
                setattr(xobj_model, key, val)
                fields.pop(key)
            elif isinstance(val, XObjHrefModel):
                val.serialize(request)
                setattr(xobj_model, key, val)

        for field in fields.keys():
            if isinstance(fields[field], related.RelatedField):
                val = getattr(self, field)
                if val:
                    href_model = type('%s_href' % \
                        self.__class__.__name__, (object,), {})()
                    href_model._xobj = xobj.XObjMetadata(
                                        attributes = {'href':str})
                    href_model.href = val.get_absolute_url(request, self.pk)
                    setattr(xobj_model, field, href_model)

        for accessor in accessors.keys():
            if hasattr(accessors[accessor].model, '_xobj') and \
               accessors[accessor].model._xobj.tag:
                    var_name = accessors[accessor].model._xobj.tag
            else:
                var_name = accessors[accessor].var_name
            accessor_model = type(accessor, (object,), {})()
            if getattr(accessors[accessor].field, 'deferred', False):
                rel_mod = getattr(self, accessor).model()
                href = rel_mod.get_absolute_url(request, self.pk)
                accessor_model._xobj = xobj.XObjMetadata(
                    attributes={'href':str})
                accessor_model.href = href
                setattr(xobj_model, accessor, accessor_model)
            else:
                accessor_model = type(accessor, (object,), {})()
                setattr(accessor_model, var_name, [])
                try:
                    for rel_mod in getattr(self, accessor).all():
                        rel_mod = rel_mod.serialize(request)
                        getattr(accessor_model, var_name).append(rel_mod)
                    setattr(xobj_model, accessor, accessor_model)
                except exceptions.ObjectDoesNotExist:
                    setattr(xobj_model, accessor, None)

        for list_field in self.list_fields:
            for val in getattr(self, list_field, []):
                val_model = val.serialize(request)
                if not hasattr(xobj_model, list_field):
                    setattr(xobj_model, list_field, [])
                getattr(xobj_model, list_field).append(val_model)

        return xobj_model

class XObjIdModel(XObjModel):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                attributes = {'id':str})

    def serialize(self, request=None):
        xobj_model = XObjModel.serialize(self, request)
        xobj_model._xobj = xobj.XObjMetadata(
                            attributes = {'id':str})
        xobj_model.id = self.get_absolute_url(request)
        return xobj_model

class XObjHrefModel(XObjModel):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                attributes = {'href':str})

    def __init__(self, href=None):
        self.href = href

    def serialize(self, request=None):
        self.href = request.build_absolute_uri(self.href)

class DeferrableForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        self.deferred = kwargs.pop('deferred', False)
        super(DeferrableForeignKey, self).__init__(*args, **kwargs)

class DateTimeUtcField(models.DateTimeField):
    def pre_save(self, model_instance, add):
        if self.auto_now or (self.auto_now_add and add):
            value = datetime.datetime.now(tz.tzutc())
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(models.DateField, self).pre_save(model_instance, add)

