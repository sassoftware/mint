#!/usr/bin/python

import datetime
from dateutil import parser
from dateutil import tz
import urlparse

from django.db import models
from django.db.models import fields as djangofields
from django.db.models.fields import related
from django.core import exceptions
from django.core import urlresolvers 

from xobj import xobj

class XObjHiddenMixIn(object):
    """
    Fields implementing this interface will not be serialized in the
    external API
    """
    XObjHidden = True

class APIReadOnlyMixIn(object):
    """
    Fields implementing this interface will not be updated through the
    external API
    """
    APIReadOnly = True

type_map = {}

class BaseManager(models.Manager):
    """
    Common manager class all models should use.  Adds ability to load a model
    from the database based on an existing model, and the ability to
    deserialize an object from xobj into an instance of the model.
    """

    def load_from_db(self, model_inst, accessors=None):
        """
        Load a model from the db based on model_inst.  Uses load_fields on the
        model to look up a corresponding model in the db. 

        Override this method for more specific behavior for a given model.
        """
        try:
            loaded_model = self.get(**model_inst.load_fields_dict())
            return loaded_model
        except exceptions.ObjectDoesNotExist:
            return None
        except exceptions.MultipleObjectsReturned:
            return None

    def load(self, model_inst, accessors=None):
        """
        Load a model based on model_inst, which is an instance of the model.
        Allows for checking to see if model_inst already exists in the db, and
        if it does returns a corresponding model with the correct fields set
        (such as pk, which wouldn't be set on model_inst).

        If a matching model was found, update it's fields with the values from
        model_inst.
        """

        loaded_model = self.load_from_db(model_inst, accessors)

        # For each field on loaded_model, see if that field is defined on
        # model_inst, if it is and the value is different, update the value on
        # loaded_model.  In this case we are most likely handling a PUT or an
        # update to a model.
        if loaded_model:
            for field in loaded_model._meta.fields:
                # Ignore pk fields
                if field.primary_key:
                    continue
                # django throws ObjectDoesNotExist if you try to access a
                # related model that doesn't exist, so just swallow it.
                try:
                    newFieldVal = getattr(model_inst, field.name, None)
                except exceptions.ObjectDoesNotExist:
                    newFieldVal = None
                if newFieldVal is None:
                    continue
                oldFieldVal = getattr(loaded_model, field.name)
                try:
                    if newFieldVal != oldFieldVal:
                        setattr(loaded_model, field.name, newFieldVal)
                except TypeError:
                    import epdb; epdb.serve()  
            return loaded_model

        return loaded_model

    def load_or_create(self, model_inst, accessors=None):
        """
        Similar in vein to django's get_or_create API.  Try to load a model
        from the db, if one wasn't found, create one and return it.
        """
        created = False
        # Load the model from the db.
        loaded_model = self.load(model_inst, accessors)
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
        Given an href, return the corresponding model.
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

    def add_fields(self, model, obj, request, save=True):
        """
        For each obj attribute, if the attribute matches a field name on
        model, set the attribute's value on model.
        """
        fields = model.get_field_dict()

        for key, val in obj.__dict__.items():
            field = fields.get(key, None)
            if field is None:
                continue
            # special case for fields that may not exist at load time or we
            # want to ignore for other reasons
            if key in model.load_ignore_fields:
                continue
            if getattr(field, 'APIReadOnly', None):
                # Ignore APIReadOnly fields
                continue
            # Special case for FK fields which should be hrefs.
            if isinstance(field, SerializedForeignKey):
                val = field.related.parent_model.objects.load_from_object(val, request, save=save)
            elif isinstance(field, InlinedForeignKey):
                lookup = { field.visible : str(val) }
                # Look up the inlined value
                val = field.related.parent_model.objects.get(**lookup)
            elif isinstance(field, related.RelatedField):
                val = field.related.parent_model.objects.load_from_href(
                    getattr(val, 'href', None))
            elif isinstance(field, djangofields.BooleanField) or \
                 isinstance(field, djangofields.NullBooleanField):
                val = str(val)
                val = (val.lower() == str(True).lower())
            elif isinstance(field, DateTimeUtcField):
                # Empty string is not valid, explicitly convert to None
                if val:
                    val = str(val)
                else:
                    val = None
            elif val is not None:
                if field.primary_key:
                    val = int(val)
                else:
                    # Cast to str, django will just do the right thing.
                    val = str(val)
                    val = field.get_prep_value(val)
            else:
                val = None

            setattr(model, key, val)

        return model

    def add_list_fields(self, model, obj, request, save=True):
        """
        For each list_field on the model, get the objects off of obj, load
        their corresponding model and add them to our model in a list.
        """
        for key in model.list_fields:
            flist = getattr(obj, key, None)
            if type(flist) != type([]):
                flist = [flist]
            mods = []
            for val in flist:
                m = type_map[key].objects.load_from_object(val, request,
                    save=save)
                mods.append(m)
            if mods:
                setattr(model, key, mods)

        return model

    def get_accessors(self, model, obj, request=None):
        """
        Build and return a dict of accessor name and list of accessor
        objects.
        """
        accessors = model.get_accessor_dict()
        ret_accessors = {}

        for key, val in obj.__dict__.items():
            if key in accessors:
                ret_accessors[key] = []
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
                    ret_accessors[key].append(rel_mod)
        return ret_accessors

    def add_accessors(self, model, accessors):
        """
        For each obj attribute, if the attribute matches an accessor name,
        load all the acccessor models off obj and add them to the model's 
        accessor.
        """
        for key, val in accessors.items():
            for v in val:
                getattr(model, key).add(v)
        return model

    def set_m2m_accessor(self, model, m2m_accessor, rel_mod):
        """
        Add rel_mod to the correct many to many accessor on model.  Needs to
        be in a seperate method so that it can be overridden.
        """
        getattr(model, m2m_accessor).add(rel_mod)

    def clear_m2m_accessor(self, model, m2m_accessor):
        """
        Clear a many to many accessor.  Needs to be in a seperate method so
        that it can be overridden.
        """
        getattr(model, m2m_accessor).clear()

    def add_m2m_accessors(self, model, obj, request):
        """
        Populate the many tom many accessors on model based on the xobj model
        in obj.
        """
        for m2m_accessor, m2m_mgr in model.get_m2m_accessor_dict().items():
            rel_obj_name = m2m_mgr.target_field_name
            self.clear_m2m_accessor(model, m2m_accessor)
            acobj = getattr(obj, m2m_accessor, None)
            objlist = getattr(acobj, rel_obj_name, None)
            if objlist is not None and not isinstance(objlist, list):
                objlist = [ objlist ]
            for rel_obj in objlist or []:
                rel_mod = type_map[rel_obj_name].objects.load_from_object(
                    rel_obj, request)
                self.set_m2m_accessor(model, m2m_accessor, rel_mod)

        return model

    def add_synthetic_fields(self, model, obj):
        # Not all models have the synthetic fields option set, so use getattr
        for fieldName in getattr(model._meta, 'synthetic_fields', []):
            val = getattr(obj, fieldName, None)
            if val is not None:
                # XXX for now we assume synthetic fields are char only.
                val = str(val)
            setattr(model, fieldName, val)
        return model

    def load_from_object(self, obj, request, save=True):
        """
        Given an object (obj) from xobj, create and return the  corresponding
        model, loading it from the db if one exists.  obj does not have to be
        from xobj, but it should match the similar structure of an object that
        xobj would create from xml.
        """
        # Every manager has access to the model it's a manager for, create an
        # empty model instance to start with.
        model = self.model()

        # Don't even attempt to save abstract models
        if model._meta.abstract:
            save = False

        # We need access to synthetic fields before loading from the DB, they
        # may be used in load_or_create
        model = self.add_synthetic_fields(model, obj)
        model = self.add_fields(model, obj, request, save=save)
        accessors = self.get_accessors(model, obj, request)
        if save:
            created, model = self.load_or_create(model, accessors)
        else:
            dbmodel = self.load(model, accessors)
            if dbmodel:
                model = dbmodel
        # Copy the synthetic fields again - this is unfortunate
        model = self.add_synthetic_fields(model, obj)

        model = self.add_m2m_accessors(model, obj, request)
        model = self.add_list_fields(model, obj, request, save=save)
        model = self.add_accessors(model, accessors)

        return model

class TroveManager(BaseManager):
    def load_from_object(self, obj, request, save=True):
        # None flavor fixup
        if getattr(obj, 'flavor', None) is None:
            obj.flavor = ''
        # Fix up the flavor in the version object
        obj.version.flavor = obj.flavor
        return BaseManager.load_from_object(self, obj, request, save=save)

    def clear_m2m_accessor(self, model, m2m_accessor):
        # We don't want available_updates to be published via REST
        if m2m_accessor == 'available_updates':
            return
        BaseManager.clear_m2m_accessor(self, model, m2m_accessor)

    def set_m2m_accessor(self, model, m2m_accessor, rel_mod):
        if m2m_accessor == 'available_updates':
            return
        return BaseManager.set_m2m_accessor(self, model, m2m_accessor, rel_mod)

class VersionManager(BaseManager):
    def add_fields(self, model, obj, request, save=True):
        # Fix up label and revision
        nmodel = BaseManager.add_fields(self, model, obj, request, save=save)
        v = nmodel.conaryVersion
        nmodel.fromConaryVersion(v)
        return nmodel

class JobManager(BaseManager):
    def load_from_db(self, model_inst, accessors):
        loaded_model = BaseManager.load_from_db(self, model_inst, accessors)
        if loaded_model:
            return loaded_model
        # We could not find the job. Create one just because we need to
        # populate some of the required fields
        model = self.model()
        mclass = type_map['job_state']
        model.job_state = mclass.objects.get(name=mclass.QUEUED)
        mclass = type_map['event_type']
        model.event_type = mclass.objects.get(name=mclass.SYSTEM_REGISTRATION)
        return model

class SystemManager(BaseManager):
    
    def load_from_db(self, model_inst, accessors):
        """
        Overridden because systems have several checks required to determine 
        if the system already exists.
        """

        # only check uuids if they are not none
        if model_inst.local_uuid and model_inst.generated_uuid:
            loaded_model = self.tryLoad(dict(local_uuid=model_inst.local_uuid,
                generated_uuid=model_inst.generated_uuid))
            if loaded_model:
                # a system matching (local_uuid, generated_uuid) was found)
                return loaded_model
        if model_inst.event_uuid:
            # Look up systems by event_uuid
            systems = [ x.system
                for x in type_map['__systemJob'].objects.filter(
                    event_uuid = model_inst.event_uuid) ]
            if systems:
                return systems[0]

        return None

    def tryLoad(self, loadDict):
        try:
            loaded_model = self.get(**loadDict)
            return loaded_model
        except exceptions.ObjectDoesNotExist:
            return None
        except exceptions.MultipleObjectsReturned:
            return None
        
        return loaded_model
    
    def clear_m2m_accessor(self, model, m2m_accessor):
        # XXX Need a better way to handle this
        if m2m_accessor in [ 'installed_software', 'system_jobs' ]:
            return
        BaseManager.clear_m2m_accessor(self, model, m2m_accessor)

    def set_m2m_accessor(self, model, m2m_accessor, rel_mod):
        # XXX Need a better way to handle this
        if m2m_accessor == 'installed_software':
            model.new_versions.append(rel_mod)
        elif m2m_accessor == 'system_jobs':
            self._handleSystemJob(model, rel_mod)
        else:
            BaseManager.set_m2m_accessor(self, model, m2m_accessor, rel_mod)

    def _handleSystemJob(self, system, job):
        self.lastJob = None
        # Validate event_uuid too - fetch SystemJob entry
        try:
            sj = job.systems.get(system__system_id=system.pk)
        except exceptions.ObjectDoesNotExist:
            return
        if sj.event_uuid != system.event_uuid:
            return
        # Update time_updated, this should in theory be the time when the
        # job completes
        job.time_updated = datetime.datetime.now(tz.tzutc())
        # XXX This just doesn't seem right
        job.save()
        # Save the job so we know to update the system state
        system.lastJob = job

class ManagementNodeManager(SystemManager):
    """
    Overridden because management nodes have several checks required to determine 
    if the system already exists.
    """

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
    # dns_name for the Network model, it could be dns_name.
    # Allows us to load a model from the db to match one we've built
    # dynamically using xobj.
    load_fields = {}
    
    # Fields that we want ignore when loading a model.  This is most often used
    # with multi-table inheritance when we are creating an object that subclasses
    # another.  We want to ignore the reference to its parent.
    load_ignore_fields = {}

    # Models that reference each other can cause infinite recursion when we
    # try to serialize them, since we serialize related objects.  Set this
    # flag to False in a model that has circular references to tell it not to
    # serialize models that refer to it with foreign keys.
    serialize_accessors = True

    old_m2m_accessors = {}

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

    def get_absolute_url(self, request=None, parent=None):
        """
        Return an absolute url for this model.  Incorporates the same behavior
        as the django decorator models.pattern, but we use it directly here so
        that we can generate absolute urls.
        """
        # Default to class name for the view_name to use during the lookup,
        # allow it to be overriden by a view_name attribute.
        view_name = getattr(self, 'view_name', self.__class__.__name__)

        # If parent wasn't specified, use our own pk, e.g., parent can be
        # specified so that when generating a url for a Network model, the
        # system parent can be sent in, such that the result is
        # /api/inventory/systems/1/networks, where 1 is the system pk.
        if not parent:
            url_key = getattr(self, 'pk', [])
        else:
            url_key = parent.pk
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

    def get_m2m_accessor_dict(self):
        """
        dict of many to many field names and their managers.
        """
        m2m_accessors = {}
        for m in self._meta.get_m2m_with_model():
            f = m[0]
            m2m_accessors[f.name] = getattr(self, f.name)
        return m2m_accessors

    def serialize_fields(self, xobj_model, fields, request):
        """
        For each attribute on self (the model), see if it's a field, if so,
        set the value on xobj_model.  Then, remove it from fields, we don't
        want to try to serialize it later.
        """
        for key, val in self.__dict__.items():
            field = fields.pop(key, None)
            if field is not None:
                if getattr(field, 'XObjHidden', False):
                    continue
                if val is None:
                        val = ''
                # Special handling of DateTimeFields.  Could make this OO by
                # calling .seriaize(...) on each field, and overriding that
                # behavior for DateTimeField's, but as long as it's just this
                # one case, we'll leave it like this.
                elif isinstance(field, models.DateTimeField):
                    val = val.replace(tzinfo=tz.tzutc())
                    val = val.isoformat()
                setattr(xobj_model, key, val)
            # TODO: is this still needed, we already called serialize_hrefs.?
            elif isinstance(val, XObjHrefModel):
                val.serialize(request)
                setattr(xobj_model, key, val)

    def serialize_fk_fields(self, xobj_model, fields, request):
        """
        For each remaining field in fields, see if it's a FK field, if so set
        the create an href object and set it on xobj_model.
        """
        for fieldName in fields:
            field = fields[fieldName]
            if isinstance(field, related.RelatedField):
                val = getattr(self, fieldName)
                serialized = getattr(field, 'serialized', False)
                visible = getattr(field, 'visible', None)
                if val:
                    if visible:
                        # If the visible prop is set, we want to copy the
                        # field's value for that property
                        setattr(xobj_model, fieldName,
                            getattr(val, visible))
                    elif not serialized:
                        href_model = type('%s_href' % \
                            self.__class__.__name__, (object,), {})()
                        href_model._xobj = xobj.XObjMetadata(
                                            attributes = {'href':str})
                        href_model.href = val.get_absolute_url(request)
                        setattr(xobj_model, fieldName, href_model)
                    else:
                        val = val.serialize(request)
                        setattr(xobj_model, fieldName, val)
                else:
                    setattr(xobj_model, fieldName, '')

    def serialize_accessors(self, xobj_model, accessors, request):
        """
        Builds up an object for each accessor for this model and sets it on
        xobj_model.  This is so that things like <networks> appear as an xml
        representation on <system> xml.
        """
        xobjHiddenAccessors =  getattr(self, '_xobj_hidden_accessors', set())
        accessorsList = [ (k, v) for (k, v) in accessors.items()
            if k not in xobjHiddenAccessors ]
        for accessorName, accessor in accessorsList:
            # Look up the name of the related model for the accessor.  Can be
            # overriden via _xobj.  E.g., The related model name for the
            # networks accessor on system is "network".
            if hasattr(accessor.model, '_xobj') and \
               accessor.model._xobj.tag:
                    var_name = accessor.model._xobj.tag
            else:
                var_name = accessor.var_name

            # Simple object to create for our accessor
            accessor_model = type(accessorName, (object,), {})()

            if getattr(accessor.field, 'deferred', False):
                # The accessor is deferred.  Create an href object for it
                # instead of a object representing the xml.
                rel_mod = getattr(self, accessorName).model()
                href = rel_mod.get_absolute_url(request, self)
                accessor_model._xobj = xobj.XObjMetadata(
                    attributes={'href':str})
                accessor_model.href = href
                setattr(xobj_model, accessorName, accessor_model)
            else:
                # In django, accessors are always lists of other models.
                setattr(accessor_model, var_name, [])
                try:
                    # For each related model in the accessor, serialize it,
                    # then append the serialized object to the list on
                    # accessor_model.
                    if isinstance(getattr(self, accessorName),
                        BaseManager):
                        for rel_mod in getattr(self, accessorName).all():
                            rel_mod = rel_mod.serialize(request)
                            getattr(accessor_model, var_name).append(rel_mod)
                    else:
                        accessor_model = None
                        continue

                    setattr(xobj_model, accessorName, accessor_model)

                # TODO: do we still need to handle this exception here? not
                # sure what was throwing it.
                except exceptions.ObjectDoesNotExist:
                    setattr(xobj_model, accessorName, None)

    def serialize_m2m_accessors(self, xobj_model, m2m_accessors, request):
        """
        Build up an object for each many to many field on this model and set
        it on xobj_model.
        """
        hidden = getattr(self, '_xobj_hidden_m2m', [])
        for m2m_accessor in m2m_accessors:
            if m2m_accessor in hidden:
                continue
            # Look up the name of the related model for the accessor.  Can be
            # overriden via _xobj.  E.g., The related model name for the
            # networks accessor on system is "network".
            if hasattr(m2m_accessors[m2m_accessor].model, '_xobj') and \
               m2m_accessors[m2m_accessor].model._xobj.tag:
                    var_name = m2m_accessors[m2m_accessor].model._xobj.tag
            else:
                var_name = \
                    m2m_accessors[m2m_accessor].model._meta.verbose_name

            # Simple object to create for our m2m_accessor
            m2m_accessor_model = type(m2m_accessor, (object,), {})()

            # In django, m2m_accessors are always lists of other models.
            setattr(m2m_accessor_model, var_name, [])
            try:
                # For each related model in the m2m_accessor, serialize
                # it, then append the serialized object to the list on
                # m2m_accessor_model.
                for rel_mod in getattr(self, m2m_accessor).all():
                    rel_mod = rel_mod.serialize(request)
                    getattr(m2m_accessor_model, var_name).append(rel_mod)

                setattr(xobj_model, m2m_accessor, m2m_accessor_model)

            # TODO: do we still need to handle this exception here? not
            # sure what was throwing it.
            except exceptions.ObjectDoesNotExist:
                setattr(xobj_model, m2m_accessor, None)

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
        m2m_accessors = self.get_m2m_accessor_dict()

        self.serialize_fields(xobj_model, fields, request)
        self.serialize_fk_fields(xobj_model, fields, request)
        if self.serialize_accessors:
            accessors = self.get_accessor_dict()
            self.serialize_accessors(xobj_model, accessors, request)
        self.serialize_m2m_accessors(xobj_model, m2m_accessors, request)
        self.serialize_list_fields(xobj_model, request)

        return xobj_model


class SyntheticField(object):
    """A field that has no database storage, but is de-serialized"""

class XObjIdModel(XObjModel):
    """
    Model that sets an id attribute on itself corresponding to the href for
    this model.
    """
    class Meta:
        abstract = True

    class __metaclass__(XObjModel.__metaclass__):
        def __new__(cls, name, bases, attrs):
            ret = XObjModel.__metaclass__.__new__(cls, name, bases, attrs)
            # Find synthetic fields
            ret._meta.synthetic_fields = synth = set()
            for k, v in attrs.items():
                if isinstance(v, SyntheticField):
                    synth.add(k)
                    # Default the value to None
                    setattr(ret, k, None)
            return ret

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

class SerializedForeignKey(models.ForeignKey):
    """
    By default, Foreign Keys serialize to hrefs. Use this field class if you
    want them to serialize to the full xml object representation instead.  Be
    careful of self referenceing models that can cause infinite recursion.
    """
    def __init__(self, *args, **kwargs):
        self.serialized = True
        super(SerializedForeignKey, self).__init__(*args, **kwargs)

class InlinedForeignKey(models.ForeignKey):
    """
    If you want a FK to be serialized as one of its fields, use the "visible"
    argument
    """
    def __init__(self, *args, **kwargs):
        self.visible = kwargs.pop('visible')
        super(InlinedForeignKey, self).__init__(*args, **kwargs)

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

    def get_prep_value(self, *args, **kwargs):
        if isinstance(args[0], basestring):
            new_args = []
            new_args.append(parser.parse(args[0]))
        else:
            new_args = args
        prep_value = super(models.DateTimeField, self).get_prep_value(
            *new_args, **kwargs)
        if isinstance(prep_value, datetime.datetime):
            return prep_value.replace(tzinfo=tz.tzutc())
        else:
            return prep_value

    def get_db_prep_value(self, *args, **kwargs):
        value = args[0]
        db_prep_value = self.get_prep_value(value)
        if isinstance(db_prep_value, datetime.datetime):
            return str(db_prep_value)
        else:
            return db_prep_value

    def to_python(self, value):
        python_value = super(DateTimeUtcField, self).to_python(value)
        if isinstance(python_value, datetime.datetime):
            return python_value.replace(tzinfo=tz.tzutc())
        else:
            return python_value

class XObjHiddenCharField(models.CharField, XObjHiddenMixIn):
    pass

class APIReadOnlyForeignKey(models.ForeignKey, APIReadOnlyMixIn):
    pass

class APIReadOnlyInlinedForeignKey(InlinedForeignKey, APIReadOnlyMixIn):
    pass
