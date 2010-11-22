#!/usr/bin/python

import datetime
from dateutil import parser
from dateutil import tz
import urlparse

from mint.lib import mintutils

from django.db import connection
from django.db import models
from django.db.models import fields as djangofields
from django.db.models.fields import related
from django.core import exceptions
from django.core import urlresolvers 

from xobj import xobj

def XObjHidden(field):
    """
    Fields implementing this interface will not be serialized in the
    external API
    """
    field.XObjHidden = True
    return field

def APIReadOnly(field):
    """
    Fields implementing this interface will not be updated through the
    external API
    """
    field.APIReadOnly = True
    return field

class DeferredForeignKeyMixIn(object):
    """
    Foreign Key that is deferred.  That means that as we enconter instances of
    this foreign key during serialization, we will create an href for the
    model instead of a full xml representation of the model.
    """
    Deferred = True

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
        keyFieldVal = None
        if model_inst._meta.has_auto_field:
            autoField = model_inst._meta.auto_field
            keyFieldName = autoField.name
            keyFieldVal = getattr(model_inst, keyFieldName, None)

        try:
            if keyFieldVal:
                loaded_model = self.get(pk=keyFieldVal)
            elif model_inst.load_fields:   
                loaded_model = self.get(**model_inst.load_fields_dict())
            else:
                return None, None
            oldModel = loaded_model.serialize()
            return oldModel, loaded_model
        except exceptions.ObjectDoesNotExist:
            return None, None
        except exceptions.MultipleObjectsReturned:
            return None, None

    def load(self, model_inst, accessors=None, withReadOnly=False):
        """
        Load a model based on model_inst, which is an instance of the model.
        Allows for checking to see if model_inst already exists in the db, and
        if it does returns a corresponding model with the correct fields set
        (such as pk, which wouldn't be set on model_inst).

        If a matching model was found, update it's fields with the values from
        model_inst.

        If withReadOnly is set to True, read-only fields will also be copied
        This should never be done when src is "unsafe" (i.e. loaded from XML)
        """

        oldModel, loaded_model = self.load_from_db(model_inst, accessors)

        # For each field on loaded_model, see if that field is defined on
        # model_inst, if it is and the value is different, update the value on
        # loaded_model.  In this case we are most likely handling a PUT or an
        # update to a model.
        if loaded_model:
            self.copyFields(loaded_model, model_inst,
                withReadOnly=withReadOnly)
            return oldModel, loaded_model

        if withReadOnly:
            # Don't touch the old model's fields even if they are read-only
            return oldModel, loaded_model

        # We need to remove the read-only fields, added from the xobj model
        for field in model_inst._meta.fields:
            if getattr(field, 'APIReadOnly', None):
                setattr(model_inst, field.name, None)
        return oldModel, loaded_model

    def copyFields(self, dest, src, withReadOnly=False):
        """
        Copy fields from src to dest
        If withReadOnly is set to True, read-only fields will also be copied
        This should never be done when src is "unsafe" (i.e. loaded from XML)
        """
        for field in dest._meta.fields:
            # Ignore pk fields
            if field.primary_key:
                continue
            if not withReadOnly and getattr(field, 'APIReadOnly', None):
                # Ignore APIReadOnly fields
                continue
            # django throws ObjectDoesNotExist if you try to access a
            # related model that doesn't exist, so just swallow it.
            try:
                newFieldVal = getattr(src, field.name, None)
            except exceptions.ObjectDoesNotExist:
                newFieldVal = None
            if newFieldVal is None:
                continue
            oldFieldVal = getattr(dest, field.name)
            if newFieldVal != oldFieldVal:
                setattr(dest, field.name, newFieldVal)

    def load_or_create(self, model_inst, accessors=None, withReadOnly=False):
        """
        Similar in vein to django's get_or_create API.  Try to load a model
        from the db, if one wasn't found, create one and return it.
        """
        # Load the model from the db.
        oldModel, loaded_model = self.load(model_inst, accessors,
            withReadOnly=withReadOnly)
        if not loaded_model:
            # No matching model was found. We need to save.  This scenario
            # means we must be creating something new (POST), so it's safe to
            # go ahead and save here, if something goes wrong later, this will
            # be automatically rolled back.
            model_inst.save()
            loaded_model = model_inst

        return oldModel, loaded_model

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
            func, args, kwargs = resolver
            # The django rest api always uses .get(...) to handle a GET, which
            # will always return a model.
            return func.get(*args, **kwargs)
        else:
            return None

    def add_fields(self, model, obj, request, save=True):
        """
        For each obj attribute, if the attribute matches a field name on
        model, set the attribute's value on model.
        """
        fields = model.get_field_dict()
        set_fields = []

        for key, val in obj.__dict__.items():
            field = fields.get(key, None)
            if field is None:
                continue
            # special case for fields that may not exist at load time or we
            # want to ignore for other reasons
            if key in model.load_ignore_fields:
                continue
            if val == '' and not val._xobj.elements \
                and not val._xobj.attributes:
                val = None
            # Special case for FK fields which should be hrefs.
            elif isinstance(field, SerializedForeignKey):
                val = field.related.parent_model.objects.load_from_object(val, request, save=save)
            elif isinstance(field, InlinedForeignKey):
                lookup = { field.visible : str(val) }
                # Look up the inlined value
                val = field.related.parent_model.objects.get(**lookup)
            elif isinstance(field, related.RelatedField):
                href = getattr(val, 'href', None)
                parentModel = field.related.parent_model
                if href is not None:
                    val = parentModel.objects.load_from_href(href)
                else:
                    # Maybe the object was inlined for convenience?
                    val = parentModel.objects.load_from_object(val, request,
                        save=save)
            elif isinstance(field, (djangofields.BooleanField,
                                    djangofields.NullBooleanField)):
                val = str(val)
                val = (val.lower() == str(True).lower())
            elif isinstance(field, djangofields.XMLField):
                if not val._xobj.elements:
                    # No children for this element
                    continue
                subelementTag = val._xobj.tag
                subelementName = val._xobj.elements[0]
                subelement = getattr(val, subelementName, None)
                if subelement is None:
                    continue
                val = xobj.toxml(subelement, tag=subelementTag,
                    prettyPrint=False, xml_declaration=False)
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

            set_fields.append(key)
            setattr(model, key, val)

        # Preserves values that might already be in the db when we load an
        # object.  We don't want the default values for fields being set on
        # model.
        for field in model._meta.fields:
            try:
                value = getattr(model, field.name, None)
            except exceptions.ObjectDoesNotExist:
                continue
            if value is not None and field.name not in set_fields:
                default_val = field.get_default()
                if default_val == '' and not hasattr(obj, field.name):
                    setattr(model, field.name, None)

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
                # We force a save here, even if the parent object was
                # abstract.
                # XXX the save keyword should be redesigned, I thought it
                # meant something else - passing it around was not a good
                # idea -- misa
                m = type_map[key].objects.load_from_object(val, request,
                    save=True)
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
            oldModel, model = self.load_or_create(model, accessors)
        else:
            oldModel, dbmodel = self.load(model, accessors)
            if dbmodel:
                model = dbmodel
        # Copy the synthetic fields again - this is unfortunate
        model = self.add_synthetic_fields(model, obj)

        model = self.add_m2m_accessors(model, obj, request)
        model = self.add_list_fields(model, obj, request, save=save)
        model = self.add_accessors(model, accessors)
        model.oldModel = oldModel

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

    def add_fields(self, model, obj, request, save=True):
        nmodel = BaseManager.add_fields(self, model, obj, request, save=save)
        if nmodel.flavor is None:
            nmodel.flavor = ''
        return nmodel

class VersionManager(BaseManager):
    def add_fields(self, model, obj, request, save=True):
        # Fix up label and revision
        nmodel = BaseManager.add_fields(self, model, obj, request, save=save)
        v = nmodel.conaryVersion
        nmodel.fromConaryVersion(v)
        if nmodel.flavor is None:
            nmodel.flavor = ''
        return nmodel

class JobManager(BaseManager):
    def load_from_db(self, model_inst, accessors):
        oldModel, loaded_model = BaseManager.load_from_db(self, model_inst, accessors)
        if loaded_model:
            return oldModel, loaded_model
        # We could not find the job. Create one just because we need to
        # populate some of the required fields
        model = self.model()
        mclass = type_map['job_state']
        model.job_state = mclass.objects.get(name=mclass.QUEUED)
        mclass = type_map['event_type']
        model.event_type = mclass.objects.get(name=mclass.SYSTEM_REGISTRATION)
        return oldModel, model

class CredentialsManager(BaseManager):
    def load_from_object(self, obj, request, save=False):
        model = self.model(system=None)
        for k, v in obj.__dict__.items():
            setattr(model, k, v)
        return model
    
class ConfigurationManager(BaseManager):
    def load_from_object(self, obj, request, save=False):
        model = self.model(system=None)
        for k, v in obj.__dict__.items():
            setattr(model, k, v)
        return model
    
class ConfigurationDescriptorManager(BaseManager):
    def load_from_object(self, obj, request, save=False):
        model = self.model(system=None)
        for k, v in obj.__dict__.items():
            setattr(model, k, v)
        return model

class SystemManager(BaseManager):
    
    def load_from_db(self, model_inst, accessors):
        """
        Overridden because systems have several checks required to determine 
        if the system already exists.
        """

        if model_inst.system_id is not None:
            loaded_model = self.tryLoad(dict(system_id=model_inst.system_id))
            if loaded_model:
                return loaded_model.serialize(), loaded_model
        # only check uuids if they are not none
        if model_inst.local_uuid and model_inst.generated_uuid:
            loaded_model = self.tryLoad(dict(local_uuid=model_inst.local_uuid,
                generated_uuid=model_inst.generated_uuid))
            if loaded_model:
                # a system matching (local_uuid, generated_uuid) was found)
                return loaded_model.serialize(), loaded_model
        if model_inst.event_uuid:
            # Look up systems by event_uuid
            systems = [ x.system
                for x in type_map['__systemJob'].objects.filter(
                    event_uuid = model_inst.event_uuid) ]
            if systems:
                system = systems[0]
                return system.serialize(), system
        if model_inst.boot_uuid:
            # Look up systems by old-style jobs
            cu = connection.cursor()
            if model_inst.target_system_id:
                cu.execute("""
                    SELECT job_system.system_id
                      FROM job_system
                      JOIN jobs USING (job_id)
                      JOIN inventory_system
                            ON (job_system.system_id = inventory_system.system_id)
                     WHERE jobs.job_uuid = %s
                       AND inventory_system.target_system_id = %s
                """, [ model_inst.boot_uuid, model_inst.target_system_id ])
            else:
                cu.execute("""
                    SELECT job_system.system_id
                      FROM job_system
                      JOIN jobs USING (job_id)
                     WHERE jobs.job_uuid = %s
                """, [ model_inst.boot_uuid ])
            rs = list(cu)
            if rs:
                loaded_model = self.tryLoad(dict(system_id=rs[0][0]))
                return loaded_model.serialize(), loaded_model
        if model_inst.target and model_inst.target_system_id:
            loaded_model = self.tryLoad(dict(target=model_inst.target,
                target_system_id=model_inst.target_system_id))
            if loaded_model:
                return loaded_model.serialize(), loaded_model

        return None, None

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
        if m2m_accessor in [ 'installed_software', 'jobs' ]:
            return
        BaseManager.clear_m2m_accessor(self, model, m2m_accessor)

    def set_m2m_accessor(self, model, m2m_accessor, rel_mod):
        # XXX Need a better way to handle this
        if m2m_accessor == 'installed_software':
            if model.new_versions is None:
                model.new_versions = []
            model.new_versions.append(rel_mod)
        elif m2m_accessor == 'jobs':
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

    def add_accessors(self, model, accessors):
        """
        Overridden here, b/c we always clear out the existing networks before
        setting new ones.
        """
        for key, val in accessors.items():
            if key == 'networks':
                model.networks.all().delete()
            for v in val:
                getattr(model, key).add(v)
        return model

class ManagementNodeManager(SystemManager):
    """
    Overridden because management nodes have several checks required to
    determine if the system already exists.
    """
    def load_from_db(self, model_inst, accessors):
        oldModel, loaded_model = BaseManager.load_from_db(self, model_inst, accessors)
        if loaded_model:
            if loaded_model.managing_zone_id is None:
                loaded_model.managing_zone = loaded_model.zone
            return oldModel, loaded_model
        model = self.model()
        model.managing_zone = model_inst.zone
        model.zone = model_inst.zone
        model.save()
        return None, model

    def getZone(self, zoneName):
        zclass = type_map['zone']
        zones = zclass.objects.filter(name=zoneName)
        if len(zones):
            return zones[0]
        # Create the zone
        zone = zclass(name=zoneName)
        zone.save()
        return zone

class SystemsManager(BaseManager):
    def load(self, model_inst, accessors=None):
        """
        Overridden because systems has no direct representation in the db - we
        need to load individual objects
        """
        model = self.model()
        return None, model

class ManagementNodesManager(SystemsManager):
    pass

class InstalledSoftwareManager(SystemsManager):
    pass

class XObjModel(models.Model):
    """
    Common model class all models should inherit from.  Overrides the default
    manager on a model with our BaseManager.  Implements get_absolute_url on
    all models.  Adds ability to serialize a model to xml using xobj.
    """
    class __metaclass__(models.Model.__metaclass__):
        def __new__(cls, name, bases, attrs):
            ret = models.Model.__metaclass__.__new__(cls, name, bases, attrs)
            # Create the xobj class for this model
            underscoreName = mintutils.Transformations.strToUnderscore(
                name[0].lower() + name[1:])
            ret._xobjClass = type(underscoreName, (object, ), {})
            return ret

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

    def __init__(self, *args, **kwargs):    
        models.Model.__init__(self, *args, **kwargs)

        # Clear out any values for list_fields, so they're not shared among
        # individual instances of this class.
        for list_field in self.list_fields:
            setattr(self, list_field, [])

    def __setattr__(self, attr, val):
        """
        Hack since django has no support for timezones.  Whenever we set an
        attribute, check to see if it's a field that it is a DateTimeField, if
        so, call the to_python method on the field with the value.  If we're
        using our DateTimeUtcField subclass, the timezone will be set to utc.
        """
        field = self.get_field_dict().get(attr, None)
        if field:
            if isinstance(field, models.DateTimeField):
                val = field.to_python(val)
        object.__setattr__(self, attr, val)

    # The camelCase here is intentional - these are not extensions of django
    @classmethod
    def iterRegularFields(cls):
        for f in cls._meta.fields:
            if not isinstance(f, ForeignKey):
                yield f

    @classmethod
    def iterForeignKeys(cls):
        for f in cls._meta.fields:
            if isinstance(f, ForeignKey):
                yield f

    @classmethod
    def iterAccessors(cls, withHidden=True):
        for r in cls._meta.get_all_related_objects():
            if withHidden or \
                    r.get_accessor_name() not in getattr(cls, '_xobj_hidden_accessors', []):
                yield r

    @classmethod
    def iterM2MAccessors(cls, withHidden=True):
        for m in cls._meta.get_m2m_with_model():
            f = m[0]
            if withHidden or \
                    f.name not in getattr(cls, '_xobj_hidden_m2m', []):
                yield f

    @classmethod
    def getAccessorName(cls, accessor):
        if hasattr(accessor.model, '_xobj') and accessor.model._xobj.tag:
            return accessor.model._xobj.tag
        return accessor.var_name

    @classmethod
    def getM2MName(cls, m2model):
        if hasattr(m2model, '_xobj') and m2model._xobj.tag:
            return m2model._xobj.tag
        return m2model._meta.verbose_name

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

    def get_absolute_url(self, request=None, parents=None, model=None):
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
        if not parents:
            url_key = getattr(self, 'pk', [])
            url_key = [str(url_key)]
        else:
            url_key = []
            for parent in parents:
                url_key.append(str(parent.pk))

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

    def serialize_fields(self, xobj_model, fields, request, values=None):
        """
        For each attribute on self (the model), see if it's a field, if so,
        set the value on xobj_model.  Then, remove it from fields, as don't
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
                elif isinstance(field, (djangofields.BooleanField,
                                        djangofields.NullBooleanField)):
                    val = str(val).lower()
                elif isinstance(field, djangofields.XMLField):
                    if val is None:
                        continue
                    val = xobj.parse(val)
                setattr(xobj_model, key, val)
            # TODO: is this still needed, we already called serialize_hrefs.?
            elif isinstance(val, XObjHrefModel):
                val.serialize(request)
                setattr(xobj_model, key, val)

    def serialize_fk_fields(self, xobj_model, fields, request, values=None):
        """
        For each remaining field in fields, see if it's a FK field, if so set
        the create an href object and set it on xobj_model.
        """
        for fieldName in fields:
            field = fields[fieldName]
            if getattr(field, 'XObjHidden', False):
                continue
            if isinstance(field, related.RelatedField):
                if values is None:
                    val = getattr(self, fieldName)
                else:
                    val = values.get(fieldName, None)
                text_field = getattr(field, 'text_field', None)
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
                        if text_field and getattr(val, text_field):
                            href_model._xobj.text = getattr(val, text_field)
                        setattr(xobj_model, fieldName, href_model)
                    else:
                        val = val.serialize(request)
                        setattr(xobj_model, fieldName, val)
                else:
                    setattr(xobj_model, fieldName, '')

    def serialize_accessors(self, xobj_model, accessors, request, values=None):
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
            var_name = self.getAccessorName(accessor)

            # Simple object to create for our accessor
            accessor_model = type(accessorName, (object,), {})()

            if getattr(accessor.field, 'Deferred', False):
                # The accessor is deferred.  Create an href object for it
                # instead of a object representing the xml.
                rel_mod = getattr(self, accessorName).model()
                href = rel_mod.get_absolute_url(request, parents=[self])
                accessor_model._xobj = xobj.XObjMetadata(
                    attributes={'href':str})
                accessor_model.href = href
                setattr(xobj_model, accessorName, accessor_model)
            else:
                # In django, accessors are always lists of other models.
                accessorModelValues = []
                setattr(accessor_model, var_name, accessorModelValues)
                try:
                    # For each related model in the accessor, serialize it,
                    # then append the serialized object to the list on
                    # accessor_model.
                    if values is None:
                        accessorValues = getattr(self, accessorName)
                        if isinstance(accessorValues, BaseManager):
                            accessorValues = [ (x, None)
                                for x in accessorValues.all() ]
                        else:
                            accessorValues = None
                    else:
                        accessorValues = values.get(accessorName)
                    if accessorValues is not None:
                        for rel_mod, subvalues in accessorValues:
                            rel_mod = rel_mod.serialize(request, values=subvalues)
                            accessorModelValues.append(rel_mod)
                    else:
                        accessor_model = None

                    setattr(xobj_model, accessorName, accessor_model)

                # TODO: do we still need to handle this exception here? not
                # sure what was throwing it.
                except exceptions.ObjectDoesNotExist:
                    setattr(xobj_model, accessorName, None)

    def _m2m_buildXobjModel(self, request, m2m_accessor):
        dmodel = type_map.get(m2m_accessor)
        if dmodel is not None:
            m2m_accessor_model = dmodel._xobjClass()
            _xobj = getattr(dmodel, '_xobj', None)
            if _xobj is not None:
                m2m_accessor_model._xobj = _xobj
                if 'id' in _xobj.attributes:
                    m = dmodel()
                    m2m_accessor_model.id = m.get_absolute_url(request,
                        parents=[self])
        else:
            m2m_accessor_model = type(m2m_accessor, (object,), {})()
        return m2m_accessor_model

    def serialize_m2m_accessors(self, xobj_model, m2m_accessors, request,
            values=None):
        """
        Build up an object for each many to many field on this model and set
        it on xobj_model.
        """
        hidden = getattr(self, '_xobj_hidden_m2m', [])
        for m2m_accessor in m2m_accessors:
            if m2m_accessor in hidden:
                continue
            m2model = m2m_accessors[m2m_accessor].model
            # Look up the name of the related model for the accessor.  Can be
            # overriden via _xobj.  E.g., The related model name for the
            # networks accessor on system is "network".
            var_name = self.getM2MName(m2model)

            # Simple object to create for our m2m_accessor
            m2m_accessor_model = self._m2m_buildXobjModel(request, m2m_accessor)

            # In django, m2m_accessors are always lists of other models.
            accessorModelValues = []
            setattr(m2m_accessor_model, var_name, accessorModelValues)
            try:
                # For each related model in the m2m_accessor, serialize
                # it, then append the serialized object to the list on
                # m2m_accessor_model.
                if values is None:
                    accessorValues = [ (x, None)
                        for x in getattr(self, m2m_accessor).all() ]
                else:
                    accessorValues = values.get(m2m_accessor, [])
                for rel_mod, subvalues in accessorValues:
                    rel_mod = rel_mod.serialize(request, values=subvalues)
                    accessorModelValues.append(rel_mod)

                setattr(xobj_model, m2m_accessor, m2m_accessor_model)

            # TODO: do we still need to handle this exception here? not
            # sure what was throwing it.
            except exceptions.ObjectDoesNotExist:
                setattr(xobj_model, m2m_accessor, None)

    def serialize_list_fields(self, xobj_model, request, values=None):
        """
        Special handling of list_fields.  For each field in list_fields, get
        the list found at the attribute on the model and serialize each model
        found in that list.  Set a list of the serialized models on
        xobj_model.
        """
        for list_field in self.list_fields:
            listFieldVals = []
            setattr(xobj_model, list_field, listFieldVals)
            for val in getattr(self, list_field, []):
                if hasattr(val, '_meta'):
                    # This is a db model
                    xobjModelVal = val.serialize(request)
                else:
                    xobjModelVal = val
                listFieldVals.append(xobjModelVal)

    def serialize(self, request=None, values=None):
        """
        Serialize this model into an object that can be passed blindly into
        xobj to produce the xml that we require.
        """
        self._serialize_hrefs(request)
        # Basic object to use to send to xobj.
        xobjModelClass = self._xobjClass
        xobj_model = xobjModelClass()

        fields = self.get_field_dict()
        m2m_accessors = self.get_m2m_accessor_dict()

        self.serialize_fields(xobj_model, fields, request, values=values)
        self.serialize_fk_fields(xobj_model, fields, request, values=values)
        if self.serialize_accessors:
            accessors = self.get_accessor_dict()
            self.serialize_accessors(xobj_model, accessors, request,
                values=values)
        self.serialize_m2m_accessors(xobj_model, m2m_accessors, request,
            values=values)
        self.serialize_list_fields(xobj_model, request, values=values)

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

    def serialize(self, request=None, values=None):
        xobj_model = XObjModel.serialize(self, request, values=values)
        xobj_model._xobj = xobj.XObjMetadata(
                            attributes = {'id':str})
        xobj_model.id = self.get_absolute_url(request, model=xobj_model)
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

    def serialize(self, request=None, values=None):
        self.href = request.build_absolute_uri(self.href)
        
class ForeignKey(models.ForeignKey):
    """
    Wrapper of django foreign key for use in models
    """
    def __init__(self, *args, **kwargs):
        #
        # text_field is used when serializing the href.  It is the name of the 
        # property to use for node text.  For example, a zone with name zone1
        # serialized as an href would be <zone href="somehost/api/inventory/zones/1"/>.  
        # If you set text_field to be name, it would be <zone href="somehost/api/inventory/zones/1">zone1</zone>.
        #
        self.text_field = None
        try:
            self.text_field = kwargs.pop('text_field')
        except KeyError:
            pass # text wasn't specified, that is fine
        super(ForeignKey, self).__init__(*args, **kwargs)

class SerializedForeignKey(ForeignKey):
    """
    By default, Foreign Keys serialize to hrefs. Use this field class if you
    want them to serialize to the full xml object representation instead.  Be
    careful of self referenceing models that can cause infinite recursion.
    """
    def __init__(self, *args, **kwargs):
        self.text_field = None
        self.serialized = True
        super(SerializedForeignKey, self).__init__(*args, **kwargs)

class InlinedForeignKey(ForeignKey):
    """
    If you want a FK to be serialized as one of its fields, use the "visible"
    argument
    """
    def __init__(self, *args, **kwargs):
        self.text_field = None
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
        try:
            # Try to parse the value as a datetime.  We do this b/c django's
            # to_python parse logic does not support timezones, so it will
            # always fail.  If we can get parser.parse() to return us a
            # datetime, django's to_pyhon will be happy.
            if isinstance(value, basestring):
                value = parser.parse(value)
        except ValueError:
            # We tried to parse it as a datetime, it didn't work, so we know
            # the super()'s to_python will fail from django, so just pass here
            # and let that exception be raised.
            pass
        python_value = super(DateTimeUtcField, self).to_python(value)
        if isinstance(python_value, datetime.datetime):
            return python_value.replace(tzinfo=tz.tzutc())
        else:
            return python_value

class DeferredForeignKey(ForeignKey, DeferredForeignKeyMixIn):
    pass

class InlinedDeferredForeignKey(InlinedForeignKey, DeferredForeignKeyMixIn):
    pass

class Cache(object):
    """
    Global cache for some immutable tables
    You can access it like this:
    Cache.get(modelClass, pk=1)
    Cache.get(modelClass, name='jobtype1')
    """
    _cache = {}

    # XXX Error checking!!!
    class _CacheOne(object):
        def __init__(self, values):
            self._pk = dict((x.pk, x) for x in values)
            self._maps = {}

        def get(self, keyName, keyValue):
            if keyName == 'pk':
                return self._pk[keyValue]
            if keyName not in self._maps:
                self._maps[keyName] = dict((getattr(obj, keyName), obj)
                    for obj in self._pk.values())
            return self._maps[keyName][keyValue]

        def all(self):
            return self._pk.values()

    @classmethod
    def _getCachedClass(cls, modelClass):
        cached = cls._cache.get(modelClass, None)
        if cached is None:
            cached = cls._cache[modelClass] = cls._cacheData(modelClass)
        return cached

    @classmethod
    def get(cls, modelClass, **kwargs):
        cached = cls._getCachedClass(modelClass)
        keyName, keyValue = kwargs.items()[0]
        return cached.get(keyName, keyValue)

    @classmethod
    def all(cls, modelClass):
        return cls._getCachedClass(modelClass).all()

    @classmethod
    def reset(cls):
        cls._cache.reset()

    @classmethod
    def _cacheData(cls, modelClass):
        return cls._CacheOne(modelClass.objects.all())
