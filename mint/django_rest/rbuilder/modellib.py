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
    """
    Common manager class all models should use.  Adds ability to load a model
    from the database baesd on an existing model, and the ability to
    deserialize an object from xobj into an instance of the model.
    """

    def load_from_db(self, model_inst):
        """
        Load a model from the db based on model_inst.  Uses load_fields on the
        model to look up a corrosponding model in the db. 

        Override this method for more specific behavior for a given model.
        """
        try:
            loaded_model = self.get(**model_inst.load_fields_dict())
            return loaded_model
        except exceptions.ObjectDoesNotExist:
            return None
        except exceptions.MultipleObjectsReturned:
            return None


    def load(self, model_inst):
        """
        Load a model based on model_inst, which is an instance of the model.
        Allows for checking to see if model_inst already exists in the db, and
        if it does returns a corrosponding model with the correct fields set
        (such as pk, which wouldn't be set on model_inst).

        If a matching model was found, update it's fields with the values from
        model_inst.
        """

        loaded_model = self.load_from_db(model_inst)

        # For each field on loaded_model, see if that field is defined on
        # model_inst, if it is and the value is different, update the value on
        # loaded_model.  In this case we are most likely handling a PUT or an
        # update to a model.
        if loaded_model:
            for field in loaded_model._meta.fields:
                # django throws ObjectDoesNotExist if you try to access a
                # related model that doesn't exist, so just swallow it.
                try:
                    if getattr(model_inst, field.name) is None:
                        continue
                except exceptions.ObjectDoesNotExist:
                    continue
                if getattr(model_inst, field.name) != \
                   getattr(loaded_model, field.name):
                    setattr(loaded_model, field.name, 
                        getattr(model_inst, field.name))
            return loaded_model

        return loaded_model

    def load_or_create(self, model_inst):
        """
        Similar in vein to django's get_or_create API.  Try to load a model
        from the db, if one wasn't found, create one and return it.
        """
        created = False
        # Load the model from the db.
        loaded_model = self.load(model_inst)
        if not loaded_model:
            # No matching model was found. We need to save.  This scenario
            # means we must be creating something new (POST), so it's safe to
            # go ahead and save here, if something goes wrong later, this will
            # be automatically rolled back.
            model_inst.save()
            created = True
            loaded_model = model_inst

        return created, loaded_model

    def load_from_href(self, href):
        """
        Given an href, return the corrosponding model.
        """
        if href:
            path = urlparse.urlparse(href)[2]
            # Look up the view function that corrosponds to the href using the
            # django API.
            resolver = urlresolvers.resolve(path)
            # resolver contains a function and it's arguments that django
            # would use to call the view.
            func, args = resolver[0:2]
            # The django rest api always uses .get(...) to handle a GET, which
            # will always return a model.
            return func.get(*args)
        else:
            return None

    def add_fields(self, model, obj):
        """
        For each obj attribute, if the attribute matches a field name on
        model, set the attribute's value on model.
        """
        fields = model.get_field_dict()

        for key, val in obj.__dict__.items():
            if key in fields.keys():
                # Special case for FK fields which should be hrefs.
                if isinstance(fields[key], related.RelatedField):
                    val = fields[key].related.parent_model.objects.load_from_href(
                        getattr(val, 'href', None))
                elif val:
                    if fields[key].primary_key:
                        val = int(val)
                    else:
                        # Cast to str, django will just do the right thing.
                        val = str(val)
                else:
                    val = None

                setattr(model, key, val)

        return model

    def add_accessors(self, model, obj, request=None):
        """
        For each obj attribute, if the attribute matches an accessor name,
        load all the acccessor models off obj and add them to the model's 
        accessor.
        """
        accessors = model.get_accessor_dict()

        for key, val in obj.__dict__.items():
            if key in accessors.keys():
                rel_obj_name = accessors[key].var_name
                rel_objs = getattr(val, rel_obj_name, None)
                if rel_objs is None:
                    continue
                if type(rel_objs) != type([]):
                    rel_objs = [rel_objs]
                for rel_obj in rel_objs:
                    # We're creating related models, such as a network model
                    # that's going to reference a system, well since system is
                    # not yet set as  FK, we can't save the network model yet,
                    # so pass False for the save flag.
                    rel_mod = type_map[rel_obj_name].objects.load_from_object(
                        rel_obj, request, save=False)
                    getattr(model, key).add(rel_mod)
        return model

    def load_from_object(self, obj, request, save=True):
        """
        Given an object (obj) from xobj, create and return the  corrosponding
        model, loading it from the db if one exists.  obj does not have to be
        from xobj, but it should match the similar structure of an object that
        xobj would create from xml.
        """
        # Every manager has access to the model it's a manager for, create an
        # emtpy model instance to start with.
        model = self.model()

        model = self.add_fields(model, obj)
        if save:
            created, model = self.load_or_create(model)

        model = self.add_accessors(model, obj, request)

        return model

    
class XObjModel(models.Model):
    """
    Common model class all models should inherit from.  Overrides the default
    manager on a model with our BaseManager.  Implements get_absolute_url on
    all models.  Adds ability to serialize a model to xml using xobj.
    """
    class Meta:
        abstract = True

    # All models use our BaseManager as their manager
    objects = BaseManager()

    # Fields which should be serialized/deserialized as lists.  This is a hint
    # for the to_xml method, e.g., given the Systems model with 'system' in
    # list_fields, it knows to look for a system attribute which is a list of
    # System model.
    list_fields = []

    # Fields which can be used to uniquely load this model from the db, e.g.,
    # public_dns_name for the Network model, it could be public_dns_name.
    # Allows us to load a model from the db to match one we've built
    # dynamically using xobj.
    load_fields = {}

    def load_fields_dict(self):
        """
        Returns a dict of field name, field value for each field in
        load_fields.
        """
        fields_dict = {}
        for f in self.load_fields:
            fields_dict[f.name] = getattr(self, f.name, None)
        return fields_dict

    def to_xml(self, request=None):
        """
        Returns the xml serialization of this model.
        """
        xobj_model = self.serialize(request)
        return xobj.toxml(xobj_model, xobj_model.__class__.__name__)

    def get_absolute_url(self, request=None, pk=None):
        """
        Return an absolute url for this model.  Incorporates the same behavior
        as the django decorator models.pattern, but we use it directly here so
        that we can generate absolute urls.
        """
        # Default to class name for the view_name to use during the lookup,
        # allow it to be overriden by a view_name attribute.
        view_name = getattr(self, 'view_name', self.__class__.__name__)

        # If pk wasn't specified, use our own pk, e.g., pk can be specified so
        # that when generating a url for a Network model, the system pk can be
        # sent in, such that the result is /api/inventory/systems/1/networks,
        # where 1 is the system pk.
        if not pk:
            url_key = getattr(self, 'pk', [])
        else:
            url_key = pk
        if url_key:
            url_key = [str(url_key)]

        # Now do what models.pattern does.
        bits = (view_name, url_key)
        try:
            relative_url = urlresolvers.reverse(bits[0], None, *bits[1:3])
        except urlresolvers.NoReverseMatch:
            return None

        # Use the request to build an absolute url.
        if request:
            return request.build_absolute_uri(relative_url)
        else:
            return relative_url

    def _serialize_hrefs(self, request=None):
        """
        Serialize each occurence of where an XObjHrefModel has been set as
        an attribute on this model.
        """
        href_fields = [(f, v) for f, v in self.__class__.__dict__.items() \
                        if isinstance(v, XObjHrefModel)]
        for href in href_fields:
            href[1].serialize(request)

    def get_field_dict(self):
        """
        return dict of field names and field instances (these are not field
        values)
        """
        fields = {}
        for f in self._meta.fields:
            fields[f.name] = f
        return fields

    def get_accessor_dict(self):
        """
        dict of accessor names and instances.  an accessor in django are the
        reverse foreign key relationships, e.g., network has a FK to system,
        so system models have a system.networks attribute which refers to
        all network models that reference that system.
        """
        accessors = {}
        for r in self._meta.get_all_related_objects():
            accessors[r.get_accessor_name()] = r
        return accessors

    def serialize_fields(self, xobj_model, fields, request):
        """
        For each attribute on self (the model), see if it's a field, if so,
        set the value on xobj_model.  Then, remove it from fields, we don't
        want to try to serialize it later.
        """
        for key, val in self.__dict__.items():
            if key in fields.keys():
                if val is None:
                        val = ''
                # Special handling of DateTimeFields.  Could make this OO by
                # calling .seriaize(...) on each field, and overriding that
                # behavior for DateTimeField's, but as long as it's just this
                # one case, we'll leave it like this.
                elif isinstance(fields[key], models.DateTimeField):
                    val = val.replace(tzinfo=tz.tzutc())
                    val = val.isoformat()
                setattr(xobj_model, key, val)
                fields.pop(key)
            # TODO: is this still needed, we already called serialize_hrefs.?
            elif isinstance(val, XObjHrefModel):
                val.serialize(request)
                setattr(xobj_model, key, val)

    def serialize_fk_fields(self, xobj_model, fields, request):
        """
        For each remaining field in fields, see if it's a FK field, if so set
        the create an href object and set it on xobj_model.
        """
        for field in fields.keys():
            if isinstance(fields[field], related.RelatedField):
                val = getattr(self, field)
                if val:
                    href_model = type('%s_href' % \
                        self.__class__.__name__, (object,), {})()
                    href_model._xobj = xobj.XObjMetadata(
                                        attributes = {'href':str})
                    href_model.href = val.get_absolute_url(request)
                    setattr(xobj_model, field, href_model)

    def serialize_accessors(self, xobj_model, accessors, request):
        """
        Builds up an object for each accessor for this model and sets it on
        xobj_model.  This is so that things like <networks> appear as an xml
        representation on <system> xml.
        """
        for accessor in accessors.keys():
            # Look up the name of the related model for the accessor.  Can be
            # overriden via _xobj.  E.g., The related model name for the
            # networks accessor on system is "network".
            if hasattr(accessors[accessor].model, '_xobj') and \
               accessors[accessor].model._xobj.tag:
                    var_name = accessors[accessor].model._xobj.tag
            else:
                var_name = accessors[accessor].var_name

            # Simple object to create for our accessor
            accessor_model = type(accessor, (object,), {})()

            if getattr(accessors[accessor].field, 'deferred', False):
                # The accessor is deferred.  Create an href object for it
                # instead of a object representing the xml.
                rel_mod = getattr(self, accessor).model()
                href = rel_mod.get_absolute_url(request, self.pk)
                accessor_model._xobj = xobj.XObjMetadata(
                    attributes={'href':str})
                accessor_model.href = href
                setattr(xobj_model, accessor, accessor_model)
            else:
                # In django, accessors are always lists of other models.
                setattr(accessor_model, var_name, [])
                try:
                    # For each related model in the accessor, serialize it,
                    # then append the serialized object to the list on
                    # accessor_model.
                    for rel_mod in getattr(self, accessor).all():
                        rel_mod = rel_mod.serialize(request)
                        getattr(accessor_model, var_name).append(rel_mod)

                    setattr(xobj_model, accessor, accessor_model)

                # TODO: do we still need to handle this exception here? not
                # sure what was throwing it.
                except exceptions.ObjectDoesNotExist:
                    setattr(xobj_model, accessor, None)

    def serialize_list_fields(self, xobj_model, request):
        """
        Special handling of list_fields.  For each field in list_fields, get
        the list found at the attribute on the model and serialize each model
        found in that list.  Set a list of the serialized models on
        xobj_model.
        """
        for list_field in self.list_fields:
            for val in getattr(self, list_field, []):
                val_model = val.serialize(request)
                if not hasattr(xobj_model, list_field):
                    setattr(xobj_model, list_field, [])
                getattr(xobj_model, list_field).append(val_model)

    def serialize(self, request=None):
        """
        Serialize this model into an object that can be passed blindly into
        xobj to produce the xml that we require.
        """
        self._serialize_hrefs(request)
        name = self.__class__.__name__
        name = name[0].lower() + name[1:]
        # Basic object to use to send to xobj.
        xobj_model = type(name, (object,), {})()

        fields = self.get_field_dict()
        accessors = self.get_accessor_dict()

        self.serialize_fields(xobj_model, fields, request)
        self.serialize_fk_fields(xobj_model, fields, request)
        self.serialize_accessors(xobj_model, accessors, request)
        self.serialize_list_fields(xobj_model, request)

        return xobj_model

class XObjIdModel(XObjModel):
    """
    Model that sets an id attribute on itself corrosponding to the href for
    this model.
    """
    class Meta:
        abstract = True

    def serialize(self, request=None):
        xobj_model = XObjModel.serialize(self, request)
        xobj_model._xobj = xobj.XObjMetadata(
                            attributes = {'id':str})
        xobj_model.id = self.get_absolute_url(request)
        return xobj_model

class XObjHrefModel(XObjModel):
    """
    Model that serializes to an href.
    """
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                attributes = {'href':str})

    def __init__(self, href=None):
        self.href = href

    def serialize(self, request=None):
        self.href = request.build_absolute_uri(self.href)

class DeferredForeignKey(models.ForeignKey):
    """
    Foreign Key that is deferred.  That means that as we enconter instances of
    this foreign key during serialization, we will create an href for the
    model instead of a full xml representation of the model.
    """
    def __init__(self, *args, **kwargs):
        self.deferred = True
        super(DeferredForeignKey, self).__init__(*args, **kwargs)

class DateTimeUtcField(models.DateTimeField):
    """
    Like a DateTimeField, but default to using a datetime value that is set to
    utc time and utc time zone for default values.
    """
    def pre_save(self, model_instance, add):
        if self.auto_now or (self.auto_now_add and add):
            value = datetime.datetime.now(tz.tzutc())
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(models.DateField, self).pre_save(model_instance, add)

