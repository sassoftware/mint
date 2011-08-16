#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#
import types
import datetime
from dateutil import parser
from dateutil import tz
import urlparse

from django.db import connection
from django.db import models
from django.db.models import fields as djangofields
from django.db.models.fields import related
from django.db.models.signals import post_init, post_save
from django.db.utils import IntegrityError
from django.core import exceptions
from django.core import urlresolvers 

from xobj import xobj

from mint.django_rest.rbuilder import errors
from mint.lib import mintutils
from mint.lib import data as mintdata

# Dict to hold the union of all models' tags as keys, and the model class as
# values.  Needed so that there is exactly one place to look to determine what
# model class to use for deserialization of xml.  All models.py should add
# their models to this dict.
type_map = {}

def XObjHidden(field):
    """
    Fields implementing this interface will not be serialized in the
    external API
    """
    field.XObjHidden = True
    return field

def APIImmutable(field):
    """
    It's possible to write this item if not in the database but it may
    not be changed via the API thereafter.
    FIXME: TODO: NOT IMPLEMENTED YET, PLACEHOLDER!
    """
    field.APIImmutable = True
    return field

def APIReadOnly(field):
    """
    Fields implementing this interface will not be updated through the
    external API.  If new values are sent for the field, they will be ignored.
    """
    field.APIReadOnly = True
    return field

class BaseManager(models.Manager):
    """
    Common manager class all models should use.  Adds ability to load a model
    from the database based on an existing model, and the ability to
    deserialize an object from xobj into an instance of the model.
    """

    def _load_from_db(self, model_inst):
        """
        Load an existing model from the db from an existing instance of the
        model provided in model_inst.  As model representations are provided
        in xml, an instance of the model is instantiated with the correct
        field values.  The database needs to be checked to see if that
        instance has already been saved or not.

        Models will be loaded by either the primary key value on model_inst if
        one is set, or the load_fields attribute that are defined in the model
        class.

        This method returns a tuple of the serialized form of the loaded model
        and the loaded model, or (None, None) if no loaded model was found.

        Override this method for more specific behavior for a given model.
        """
        keyFieldVal = None
        if model_inst._meta.has_auto_field:
            autoField = model_inst._meta.auto_field
            keyFieldName = autoField.name
            keyFieldVal = getattr(model_inst, keyFieldName, None)

        try:
            if keyFieldVal:
                loadedModel = self.get(pk=keyFieldVal)
            elif model_inst.load_fields:   
                loadedModel = self.get(**model_inst._load_fields_dict())
            else:
                return None, None
            oldModel = loadedModel.serialize()
            return oldModel, loadedModel
        except exceptions.ObjectDoesNotExist:
            return None, None
        except exceptions.MultipleObjectsReturned:
            return None, None

    def _load(self, model_inst, xobjModel, withReadOnly=False):
        """
        Load a model based on model_inst, which is an instance of the model.
        Allows for checking to see if model_inst already exists in the db, and
        if it does returns a corresponding model with the correct fields set
        (such as pk, which wouldn't be set on model_inst).

        If a matching model was found, update it's fields with the values from
        model_inst.

        If withReadOnly is set to True, read-only fields will also be copied
        This should never be done when src is "unsafe" (i.e. loaded from XML)

        This method returns a tuple of the serialized form of the loaded model
        and the loaded model, or (None, None) if no loaded model was found.
        """

        # First try to load by an id or href attribute on xobjModel.  This
        # attribute (if present) should a be the full url of the model.
        loadedModel = self._load_from_href(xobjModel)
        if loadedModel:
            oldModel = loadedModel.serialize()
        else:
            # Fall back to loading from the db by model_inst
            oldModel, loadedModel = self._load_from_db(model_inst)

        # For each field on loadedModel, see if that field is defined on
        # model_inst, if it is and the value is different, update the value on
        # loadedModel.  In this case we are most likely handling a PUT or an
        # update to a model.
        if loadedModel:
            self._copyFields(loadedModel, model_inst, xobjModel,
                withReadOnly=withReadOnly)
            return oldModel, loadedModel

        if withReadOnly:
            # Don't touch the old model's fields even if they are read-only
            return oldModel, loadedModel

        # We need to remove the read-only fields, added from the xobj model
        for field in model_inst._meta.fields:
            if getattr(field, 'APIReadOnly', None):
                setattr(model_inst, field.name, None)
        return oldModel, loadedModel

    def _copyFields(self, dest, src, xobjModel=object(), withReadOnly=False):
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

            # Make sure we don't overwrite existing values on dest with fields
            # that default to None by checking that the field was actually
            # provided on xobjModel.
            if newFieldVal is None and not hasattr(xobjModel, field.name):
                continue

            # Set the new value on dest if it differs from the old value.
            oldFieldVal = getattr(dest, field.name)
            if newFieldVal != oldFieldVal:
                setattr(dest, field.name, newFieldVal)

    def load_or_create(self, model_inst, xobjModel=None, withReadOnly=False):
        """
        Similar in vein to django's get_or_create API.  Try to load a model
        based on model_inst, if one wasn't found, create one and return it.
        """
        # Load the model from the db.
        oldModel, loaded_model = self._load(model_inst,
            xobjModel=xobjModel, withReadOnly=withReadOnly)
        if not loaded_model:
            # No matching model was found. We need to save.  This scenario
            # means we must be creating something new (POST), so it's safe to
            # go ahead and save here, if something goes wrong later, this will
            # be automatically rolled back.
            model_inst.save()
            loaded_model = model_inst

        return oldModel, loaded_model

    def _load_from_href(self, xobjModel):
        """
        Given an xobjModel, and an attribute to look at on that xobjModel for
        a url, try to load the corresponding django model identified by that
        url.
        """

        if xobjModel is None:
            return None

        # Check both href and id, preferring id.
        if hasattr(xobjModel, "id"):
            href = getattr(xobjModel, "id")
        elif hasattr(xobjModel, "href"):
            href = getattr(xobjModel, "href")
        else:
            href = None

        if href:
            path = urlparse.urlparse(href)[2]
            # Look up the view function that corresponds to the href using the
            # django API.
            resolver = urlresolvers.resolve(path)
            # resolver contains a function and it's arguments that django
            # would use to call the view.
            func, args, kwargs = resolver
            # The django rest api always uses .get(...) to handle a GET, which
            # will always return a model.
            try:
                return func.get(*args, **kwargs)
            except exceptions.ObjectDoesNotExist:
                # exception handling middleware must be intercepted
                return None
        else:
            return None

    def _add_fields(self, model, xobjModel, request, save=True):
        """
        For each xobjModel attribute, if the attribute matches a field name on
        model, set the attribute's value on model.
        """
        fields = model._get_field_dict()
        set_fields = []

        for key, val in xobjModel.__dict__.items():
            field = fields.get(key, None)

            if field is None:
                # No field, this attribute does not match a field we know
                # about.
                continue

            # special case for fields that may not exist at load time or we
            # want to ignore for other reasons
            if key in model.load_ignore_fields:
                continue

            # If val is an empty string, and it has no elements and no
            # attributes, then it's not a complex xml element, so the intent
            # is to set the new value to None on the model.
            if val == '' and not val._xobj.elements \
                and not val._xobj.attributes:
                val = None

            # Serialized foreign keys are serialized inline, so we need to
            # load the model for them based on their inline xml
            # representation.
            elif isinstance(field, SerializedForeignKey):
                val = field.related.parent_model.objects.load_from_object(val, request, save=save)

            # Foreign keys can be serialized based on a text field, or the
            # text of an xml elements, try to load the foreign key model if
            # so.
            elif isinstance(field, ForeignKey) and \
                 field.text_field is not None and \
                 str(val) is not '' and \
                 hasattr(val, "_xobj"): 
                lookup = { field.text_field : str(val) }
                # Look up the inlined value
                val = field.related.parent_model.objects.get(**lookup)

            # Handle other related fields that could be inlined.
            elif isinstance(field, related.RelatedField):
                parentModel = field.rel.to
                val = parentModel.objects.load_from_object(val, request,
                        save=save)

            # Handle different combinations of true/True, etc for
            # BooleanFields.
            elif isinstance(field, (djangofields.BooleanField,
                                    djangofields.NullBooleanField)):
                val = str(val)
                val = (val.lower() == str(True).lower())

            # Handle xml fields
            elif isinstance(field, XMLField):
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

            # DateTimeUtcFeilds can not be set to empty string.
            elif isinstance(field, DateTimeUtcField):
                # Empty string is not valid, explicitly convert to None
                if val:
                    val = str(val)
                else:
                    val = None

            # All other cases where val was specified, use Django's
            # get_prep_value, except in the case of the primary key.
            elif val is not None:
                if field.primary_key:
                    try:
                        val = int(val)
                    except:
                        # primary keys might not just be ints!
                        val = str(val)
                else:
                    # Cast to str, django will just do the right thing.
                    val = str(val)
                    val = field.get_prep_value(val)

            else:
                val = None

            set_fields.append(key)
            setattr(model, key, val)

        # Values for fields that are not provided should be preserved.
        # However, since we've instantiated the model, we've gotten the
        # default values for all fields.  Make sure those default values don't
        # get saved, overwriting existing values if they weren't actually
        # provided.
        for field in model._meta.fields:
            try:
                value = getattr(model, field.name, None)
            except exceptions.ObjectDoesNotExist:
                continue
            # There is a value, and we didn't set the field, so it wasn't
            # provided.
            if value is not None and field.name not in set_fields:
                default_val = field.get_default()
                if default_val == '' and not hasattr(xobjModel, field.name):
                    setattr(model, field.name, None)

        return model

    def _add_list_fields(self, model, xobjModel, request, save=True):
        """
        For each list_field on the model, get the objects off of xobjModel, load
        their corresponding model and add them to our model in a list.
        """
        for key in model.list_fields:
            # xobj deserializes lists by adding a list as an attribute to the
            # model named after the element.
            flist = getattr(xobjModel, key, None)
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

    def _get_accessors(self, model, xobjModel, request=None):
        """
        Build and return a dict of accessor name and list of accessor
        objects.
        """
        accessors = model._get_accessor_dict()
        ret_accessors = {}

        for key, val in xobjModel.__dict__.items():
            if key in accessors:
                ret_accessors[key] = []
                rel_obj_model = accessors[key].model
                rel_obj_name = rel_obj_model.getTag()
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

    def _add_accessors(self, model, accessors):
        """
        For each xobjModel attribute, if the attribute matches an accessor name,
        load all the acccessor models off xobjModel and add them to the model's 
        accessor.
        """
        for key, val in accessors.items():
            for v in val:
                getattr(model, key).add(v)
        return model

    def _set_m2m_accessor(self, model, m2m_accessor, rel_mod):
        """
        Add rel_mod to the correct many to many accessor on model.  Needs to
        be in a seperate method so that it can be overridden.
        """
        getattr(model, m2m_accessor).add(rel_mod)

    def _clear_m2m_accessor(self, model, m2m_accessor):
        """
        Clear a many to many accessor.  Needs to be in a seperate method so
        that it can be overridden.
        """
        getattr(model, m2m_accessor).clear()

    def _add_m2m_accessors(self, model, xobjModel, request):
        """
        Populate the many to many accessors on model based on the xobj model
        in xobjModel.
        """
        for m2m_accessor, m2m_mgr in model._get_m2m_accessor_dict().items():
            _xobj = getattr(m2m_mgr.model, '_xobj', None)
            if _xobj:
                rel_obj_name = _xobj.tag or m2m_mgr.target_field_name
            else:
                rel_obj_name = m2m_mgr.target_field_name

            acobj = getattr(xobjModel, m2m_accessor, None)
            objlist = getattr(acobj, rel_obj_name, None)
            if objlist is not None:
                self._clear_m2m_accessor(model, m2m_accessor)
                if not isinstance(objlist, list):
                    objlist = [ objlist ]
            for rel_obj in objlist or []:
                modelCls = m2m_mgr.model
                rel_mod = modelCls.objects._load_from_href(rel_obj)
                if rel_mod is None:
                    rel_mod = modelCls.objects.load_from_object(
                        rel_obj, request)
                self._set_m2m_accessor(model, m2m_accessor, rel_mod)

        return model

    def _add_synthetic_fields(self, model, xobjModel, request):
        # Not all models have the synthetic fields option set, so use getattr
        for fieldName, fmodel in getattr(model._meta, 'synthetic_fields', {}).items():
            val = getattr(xobjModel, fieldName, None)
            if val is not None:
                if isinstance(val, XObjIdModel):
                    val = self.load_from_object(val, request)
            if val is not None:
                    setattr(model, fieldName, val)
        return model

    def _add_abstract_fields(self, model, xobjModel):
        abstractFields = getattr(model._meta, 'abstract_fields', None)
        if not abstractFields:
            return model
        for fieldName, mdl in abstractFields.items():
            val = getattr(xobjModel, fieldName, None)
            if val is None:
                continue
            currentVal = getattr(model, fieldName, None)
            if currentVal is None:
                mdlinst = mdl()
                setattr(model, fieldName, mdlinst)
            else:
                mdlinst = currentVal

            mdl.objects._add_fields(mdlinst, val, request=None)
        return model


    def load_from_object(self, xobjModel, request, save=True, load=True):
        """
        Given an object (xobjModel) from xobj, create and return the  corresponding
        model.  If load is True, load the model from the db and apply the
        updates to it based on xobjModel, otherwise, always create a new model.
        
        xobjModel does not have to be from xobj, but it should match the
        similar structure of an object that xobj would create from xml.
        """
        # Every manager has access to the model it's a manager for, create an
        # empty model instance to start with.
        model = self.model()

        # Don't even attempt to save abstract models
        if model._meta.abstract:
            save = False

        # We need access to synthetic fields before loading from the DB, they
        # may be used in load_or_create
        model = self._add_synthetic_fields(model, xobjModel, request)
        model = self._add_fields(model, xobjModel, request, save=save)
        accessors = self._get_accessors(model, xobjModel, request)

        # Only try to load the model if load is True.  
        if not load:
            try:
                model.save()
            except IntegrityError, e:
                e.status = errors.BAD_REQUEST
                raise e
            oldModel = None
        elif save:
            oldModel, model = self.load_or_create(model, xobjModel)
        else:
            oldModel, dbmodel = self._load(model, xobjModel)
            if dbmodel:
                model = dbmodel

        # Copy the synthetic fields again - this is unfortunate
        model = self._add_synthetic_fields(model, xobjModel, request)

        model = self._add_m2m_accessors(model, xobjModel, request)
        model = self._add_list_fields(model, xobjModel, request, save=save)
        model = self._add_accessors(model, accessors)
        model = self._add_abstract_fields(model, xobjModel)

        # Save a reference to the oldModel on model.  This could be helpful
        # later on to detect state changes.
        model.oldModel = oldModel

        return model

class PackageJobManager(BaseManager):

    def _add_fields(self, model, obj, request, save):
        job_data = getattr(obj, "job_data", None)
        
        if job_data is not None:
            obj.__dict__.pop("job_data")
            job_data_dict = {}
            for k, v in job_data.__dict__.items():
                if not k.startswith("_"):
                    job_data_dict[k] = v
            marshalled_job_data = mintdata.marshalGenericData(job_data_dict) 
            model.job_data = marshalled_job_data

        return BaseManager._add_fields(self, model, obj, request, save)

class TroveManager(BaseManager):
    def load_from_object(self, obj, request, save=True, load=True):
        # None flavor fixup
        if getattr(obj, 'flavor', None) is None:
            obj.flavor = ''
        # Fix up the flavor in the version object
        obj.version.flavor = obj.flavor
        return BaseManager.load_from_object(self, obj, request, save=save,
            load=load)

    def _clear_m2m_accessor(self, model, m2m_accessor):
        # We don't want available_updates to be published via REST
        if m2m_accessor == 'available_updates':
            return
        BaseManager._clear_m2m_accessor(self, model, m2m_accessor)

    def _set_m2m_accessor(self, model, m2m_accessor, rel_mod):
        if m2m_accessor == 'available_updates':
            return
        return BaseManager._set_m2m_accessor(self, model, m2m_accessor, rel_mod)

    def _add_fields(self, model, obj, request, save=True):
        nmodel = BaseManager._add_fields(self, model, obj, request, save=save)
        if nmodel.flavor is None:
            nmodel.flavor = ''
        return nmodel

    def _load_from_href(self, *args, **kwargs):
        return None

class VersionManager(BaseManager):
    def _add_fields(self, model, obj, request, save=True):
        # Fix up label and revision
        nmodel = BaseManager._add_fields(self, model, obj, request, save=save)
        v = nmodel.conaryVersion
        nmodel.fromConaryVersion(v)
        if nmodel.flavor is None:
            nmodel.flavor = ''
        return nmodel

class JobManager(BaseManager):
    def _load_from_db(self, model_inst):
        oldModel, loaded_model = BaseManager._load_from_db(self, model_inst)
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
    def load_from_object(self, obj, request, save=False, load=True):
        model = self.model(system=None)
        for k, v in obj.__dict__.items():
            setattr(model, k, v)
        return model
    
class ConfigurationManager(BaseManager):
    def load_from_object(self, obj, request, save=False, load=True):
        model = self.model(system=None)
        for k, v in obj.__dict__.items():
            setattr(model, k, v)
        return model
    
class ConfigurationDescriptorManager(BaseManager):
    def load_from_object(self, obj, request, save=False, load=True):
        model = self.model(system=None)
        for k, v in obj.__dict__.items():
            setattr(model, k, v)
        return model

class SystemManager(BaseManager):
    
    def _load_from_db(self, model_inst):
        """
        Overridden because systems have several checks required to determine 
        if the system already exists.
        """

        if model_inst.system_id is not None:
            loaded_model = self.tryLoad(dict(system_id=model_inst.system_id))
            if loaded_model:
                return self._fromDb(loaded_model)
        # only check uuids if they are not none
        if model_inst.local_uuid and model_inst.generated_uuid:
            loaded_model = self.tryLoad(dict(local_uuid=model_inst.local_uuid,
                generated_uuid=model_inst.generated_uuid))
            if loaded_model:
                # a system matching (local_uuid, generated_uuid) was found
                return self._fromDb(loaded_model)
        if model_inst.event_uuid:
            # Look up systems by event_uuid
            systems = [ x.system
                for x in type_map['__systemJob'].objects.filter(
                    event_uuid = model_inst.event_uuid) ]
            if systems:
                system = systems[0]
                return self._fromDb(system)
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
                return self._fromDb(loaded_model)
        if model_inst.target and model_inst.target_system_id:
            loaded_model = self.tryLoad(dict(target=model_inst.target,
                target_system_id=model_inst.target_system_id))
            if loaded_model:
                return self._fromDb(loaded_model)

        return None, None

    def _fromDb(self, obj):
        if obj is None:
            return None, None
        obj.network_address = obj.__class__.extractNetworkAddress(obj)
        return obj.serialize(), obj

    def tryLoad(self, loadDict):
        try:
            loaded_model = self.get(**loadDict)
            return loaded_model
        except exceptions.ObjectDoesNotExist:
            return None
        except exceptions.MultipleObjectsReturned:
            return None
        
        return loaded_model
    
    def _clear_m2m_accessor(self, model, m2m_accessor):
        # XXX Need a better way to handle this
        if m2m_accessor in [ 'installed_software', 'jobs' ]:
            return
        BaseManager._clear_m2m_accessor(self, model, m2m_accessor)

    def _set_m2m_accessor(self, model, m2m_accessor, rel_mod):
        # XXX Need a better way to handle this
        if m2m_accessor == 'installed_software':
            if model.new_versions is None:
                model.new_versions = []
            model.new_versions.append(rel_mod)
        elif m2m_accessor == 'jobs':
            self._handleSystemJob(model, rel_mod)
        else:
            BaseManager._set_m2m_accessor(self, model, m2m_accessor, rel_mod)

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

    def _add_accessors(self, model, accessors):
        """
        Overridden here, b/c we always clear out the existing networks before
        setting new ones.
        """
        for key, val in accessors.items():
            if key == 'networks':
                model.networks.all().delete()
            if key == "tags":
                model.tags.all().delete()
            for v in val:
                getattr(model, key).add(v)
        return model

class ManagementNodeManager(SystemManager):
    """
    Overridden because management nodes have several checks required to
    determine if the system already exists.
    """
    def _load_from_db(self, model_inst):
        oldModel, loaded_model = BaseManager._load_from_db(self, model_inst)
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

class StubManager(BaseManager):
    def _load(self, *args, **kwargs):
        """
        Overridden because systems has no direct representation in the db - we
        need to load individual objects
        """
        model = self.model()
        return None, model

class RbacRolesManager(StubManager):
    pass

class RbacContextsManager(StubManager):
    pass

class RbacPermissionsManager(StubManager):
    pass

class RbacUserRolesManager(StubManager):
    pass

class SystemsManager(StubManager):
    pass

class ManagementNodesManager(SystemsManager):
    pass

class InstalledSoftwareManager(SystemsManager):
    pass

class ProductsManager(BaseManager):
    def _load_from_href(self, *args, **kwargs):
        return None

class XObjModel(models.Model):
    """
    Common model class all models should inherit from.  Overrides the default
    manager on a model with our BaseManager.  Implements get_absolute_url on
    all models.  Adds ability to serialize a model to xml using xobj.
    """
    class __metaclass__(models.Model.__metaclass__):
        """
        Metaclass for all models.  
        Sets the _xobjClass attribute on the class, and consolidates _xobj
        metadata across all base classes.  Such that attributes/elements in _xobj
        specified on base classes are consolidated in the subclass as opposed to
        overwritten.
        """
        def __new__(cls, name, bases, attrs):
            ret = models.Model.__metaclass__.__new__(cls, name, bases, attrs)
            # Create the xobj class for this model
            underscoreName = mintutils.Transformations.strToUnderscore(
                name[0].lower() + name[1:])
            ret._xobjClass = type(underscoreName, (object, ), {})

            retXObj = getattr(ret, '_xobj', None)
            if retXObj:
                # Inspect each base class and consolidate the attributes and
                # elements in _xobj.
                for base in bases:
                    _xobj = getattr(base, '_xobj', None)
                    if not _xobj:
                        continue
                    newAttrs = _xobj.attributes.copy()
                    newAttrs.update(ret._xobj.attributes)
                    ret._xobj.attributes = newAttrs

                    for elem in _xobj.elements:
                        if elem not in ret._xobj.elements:
                            ret._xobj.elements.append(elem)

            return ret

    class Meta:
        abstract = True

    # The manager gets set by the service when it dispatches one of the
    # HTTP methods.
    # Don't expect _rbmgr to be set when loading fixtures, for instance
    _rbmgr = None

    # All models use our BaseManager as their manager
    objects = BaseManager()

    # Fields that when changed, cause a log to get created in the changelog
    # application.
    logged_fields = []

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

    # Attribute used to look up the url for this resource, defaults to pk,
    # since we use the primary keys most of the times in the URL's.
    url_key = ['pk']

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
        field = self._get_field_dict().get(attr, None)
        if field:
            if isinstance(field, models.DateTimeField):
                val = field.to_python(val)
        object.__setattr__(self, attr, val)

    # The camelCase here is intentional - these are not extensions of django
    # NOTE: NOT USED?
    #@classmethod
    #def iterRegularFields(cls):
    #    for f in cls._meta.fields:
    #        if not isinstance(f, ForeignKey):
    #            yield f

    # NOTE: NOT USED?
    #@classmethod
    #def iterForeignKeys(cls):
    #    for f in cls._meta.fields:
    #        if isinstance(f, ForeignKey):
    #            yield f

    # NOTE: NOT USED?
    #@classmethod
    #def iterAccessors(cls, withHidden=True):
    #    for r in cls._meta.get_all_related_objects():
    #        if withHidden or \
    #                r.get_accessor_name() not in getattr(cls, '_xobj_hidden_accessors', []):
    #           yield r

    # NOTE: NOT USED?
    #@classmethod
    #def iterM2MAccessors(cls, withHidden=True):
    #    for m in cls._meta.get_m2m_with_model():
    #        f = m[0]
    #        if withHidden or \
    #                f.name not in getattr(cls, '_xobj_hidden_m2m', []):
    #            yield f

    @classmethod
    def getAccessorName(cls, accessor):
        if hasattr(accessor.model, '_xobj') and accessor.model._xobj.tag:
            return accessor.model._xobj.tag
        return accessor.var_name

    @classmethod
    def _getM2MName(cls, m2model):
        if hasattr(m2model, '_xobj') and m2model._xobj.tag:
            return m2model._xobj.tag
        return m2model._meta.verbose_name

    @classmethod
    def getTag(cls):
        tag = None
        _xobj = getattr(cls, '_xobj', None)
        if _xobj:
            tag = _xobj.tag
        if not tag:
            tag = cls.__name__.lower()
        return tag

    def _saveFields(self):
        if self._meta.abstract:
            return
        fieldNames = self._get_field_dict().keys()
        if self.pk:
            self._savedFields = dict((f, getattr(self, f)) \
                            for f in self.logged_fields \
                            if f in fieldNames)
        else:
            self._savedFields = None

    def _getChangedFields(self):
        changedFields = {}
        if self._savedFields is None:
            return changedFields
        for k, v in self._savedFields.items():
            if v != getattr(self, k):
                changedFields[k] = v
        return changedFields

    def _load_fields_dict(self):
        """
        Returns a dict of field name, field value for each field in
        load_fields.
        """
        fields_dict = {}
        for f in self.load_fields:
            fields_dict[f.name] = getattr(self, f.name, None)
        return fields_dict

    def to_xml(self, request=None, xobj_model=None):
        """
        Returns the xml serialization of this model.
        """
        if not xobj_model:
            xobj_model = self.serialize(request)
        return xobj.toxml(xobj_model, xobj_model.__class__.__name__)

    def to_json(self, request=None, xobj_model=None):
        """
        Experimental.

        Returns the json serialization of this model.
        Requires jobj module.
        """
        import jobj
        if not xobj_model:
            xobj_model = self.serialize(request)
        return jobj.tojson(xobj_model)

    def get_url_key(self):
        """
        url_key for a model refers to the field values on the model that are
        used to construct the uniquely identifying parts of the resource url.
        E.g., given /api/inventory/systems/10, 10 is the primary key on the systems
        model, thus the primary key field (pk or system_id) is the url_key for
        the systems model.
        """

        # url_key should always be a list, since potentially a resource id
        # could have multiple uniquely identifying parts.
        # E.g., network might be /api/inventory/systems/10/networks/10
        if type(self.url_key) != type([]):
            url_key = [self.url_key]
        else:
            url_key = self.url_key

        url_key_values = []
        for uk in url_key:
            if hasattr(self, uk):
                key_value = getattr(self, uk)
                # url_keys could potentially be a foreign key field, in which
                # case we need to ask that model for it's url_key.
                if hasattr(key_value, "get_url_key"):
                    url_key_values += key_value.get_url_key()
                else:   
                    url_key_values.append(str(key_value))
            else:
                # XXX do something else?
                continue

        return url_key_values

    def get_absolute_url(self, request=None, parents=None, view_name=None):
        """
        Return an absolute resource url for this model.  Incorporates the same
        behavior as the django decorator models.pattern, but we use it
        directly here so that we can generate absolute urls.
        """
        # Default to class name for the view_name to use during the lookup,
        # allow it to be overriden by a view_name attribute.
        if not view_name:
            view_name = getattr(self, 'view_name', self.__class__.__name__)

        # If parent wasn't specified, use our own pk, e.g., parent can be
        # specified so that when generating a url for a Network model, the
        # system parent can be sent in, such that the result is
        # /api/inventory/systems/1/networks, where 1 is the system pk.
        _parents = getattr(self, '_parents', parents)
        if _parents:
            url_key = []
            for parent in _parents:
                url_key += parent.get_url_key()
        else:
            url_key = self.get_url_key()

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

    def _get_field_dict(self):
        """
        return dict of field names and field instances (these are not field
        values)
        """
        fields = {}
        for f in self._meta.fields:
            fields[f.name] = f
        return fields

    def _get_accessor_dict(self):
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

    def _get_m2m_accessor_dict(self):
        """
        dict of many to many field names and their managers.
        """
        m2m_accessors = {}
        for m in self._meta.get_m2m_with_model():
            f = m[0]
            try:
                m2m_accessors[f.name] = getattr(self, f.name)
            except ValueError:
                pass
        return m2m_accessors

    def _serialize_fields(self, xobj_model, fields, request, summarize):
        """
        For each attribute on self (the model), see if it's a field, if so,
        set the value on xobj_model.  Then, remove it from fields, as don't
        want to try to serialize it later.
        """
        syntheticFields = getattr(self._meta, 'synthetic_fields', {})
        summary_fields = self._get_summary_fields() # FIXME: rename this better
        for key, val in self.__dict__.items():
            if summarize and key not in summary_fields:
                # the object was tagged for summarization and this is not one of the
                # included fields, so skip this one.
                print "skipping regular key=%s on %s" % (key,self)
                continue 
            field = fields.pop(key, None)
            if field is None:
                field = syntheticFields.get(key)
                if field is not None and val is not None:
                    # The user specified a value for the synthetic field.
                    # We'll use that instead of the one from the class def
                    field = val
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
                    val = str(bool(val)).lower()
                elif isinstance(field, XMLField):
                    if val is None:
                        continue
                    val = xobj.parse(val)
                elif isinstance(field, HrefField):
                    val = field.serialize_value(request)
                elif isinstance(field, djangofields.DecimalField):
                    val = float(val)
                elif isinstance(val, XObjModel):
                    # allow nested synthetic fields to override serialization
                    # if the child of the synthetic field is an XObjIdModel
                    val = val.serialize(request)
                setattr(xobj_model, key, val)
  
    def _get_summary_fields(self):
        '''
        Return the summary fields for an object if it's tagged for summarization,
        otherwise return None.  NOTE: there is one case (the older one) where
        things are always summarized.  This is different.  Summarize means
        "expand these FKs to include additional info", but it also is used
        to show only certain items in list fields, that are not FKs.  The former
        case doesn't require the "_summarize" detector bit.
        '''
        should_summarize = getattr(self, '_summarize', False)
        if not should_summarize:
            return None
        fields = getattr(self, 'summary_fields', None)
        if fields is None:
            return [ 'id' ]
        return fields

    def _serialize_fk_fields(self, xobj_model, fields, request):
        """
        For each remaining field in fields, see if it's a FK field, if so set
        the create an href object and set it on xobj_model.
        TODO: accessors?
        """
        summary_fields = self._get_summary_fields()
        for fieldName in fields:
            if summary_fields and fieldName not in summary_fields:
                continue
            field = fields[fieldName]
            if getattr(field, 'XObjHidden', False):
                continue
            if isinstance(field, related.RelatedField):
                val = getattr(self, fieldName)
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
                        refModel = type('%s_ref' % \
                            self.__class__.__name__, (object,), {})()
                        refModel._xobj = xobj.XObjMetadata(
                                            attributes = {"id":str})
                        setattr(refModel, "id", 
                            val.get_absolute_url(request))
                        if hasattr(val, "summary_view"):
                            for sField in val.summary_view:
                                setattr(refModel, sField, getattr(val, sField))
                        if text_field and getattr(val, text_field):
                            refModel._xobj.text = getattr(val, text_field)
                        setattr(xobj_model, fieldName, refModel)
                    else:
                        val = val.serialize(request)
                        setattr(xobj_model, fieldName, val)
                else:
                    setattr(xobj_model, fieldName, '')

    def _serialize_fk_accessors(self, xobj_model, accessors, request):
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
                rel_mod = accessor.model()
                href = rel_mod.get_absolute_url(request, parents=[self],
                    view_name=accessor.field.view_name)
                accessor_model._xobj = xobj.XObjMetadata(
                    attributes={"id":str})
                setattr(accessor_model, "id", href)
                setattr(xobj_model, accessorName, accessor_model)
            else:
                # In django, accessors are always lists of other models.
                accessorModelValues = []
                setattr(accessor_model, var_name, accessorModelValues)
                try:
                    # For each related model in the accessor, serialize it,
                    # then append the serialized object to the list on
                    # accessor_model.
                    accessorValues = getattr(self, accessorName)
                    if isinstance(accessorValues, BaseManager):
                        accessorValues = [ (x, None)
                            for x in accessorValues.all() ]
                    else:
                        accessorValues = None
                    if accessorValues is not None:
                        for rel_mod, subvalues in accessorValues:
                            rel_mod = rel_mod.serialize(request)
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

    def _serialize_m2m_accessors(self, xobj_model, m2m_accessors, request):
        """
        Build up an object for each many to many field on this model and set
        it on xobj_model.
        """
        hidden = getattr(self, '_xobj_hidden_m2m', [])
        for m2m_accessor in m2m_accessors:
            if m2m_accessor in hidden:
                continue
            deferred = getattr(self._meta.get_field(m2m_accessor), 
                "Deferred", None)
            if deferred:
                rel_mod = type_map[m2m_accessor]()
                resourceId = rel_mod.get_absolute_url(request, parents=[self])
                m2mIdModel = type(m2m_accessor, (object,), {})()
                m2mIdModel._xobj = xobj.XObjMetadata(
                    attributes={"id":str})
                m2mIdModel._xobj.tag = m2m_accessor
                m2mIdModel.id = resourceId
                setattr(xobj_model, m2m_accessor, m2mIdModel)
                continue

            m2model = m2m_accessors[m2m_accessor].model
            # Look up the name of the related model for the accessor.  Can be
            # overriden via _xobj.  E.g., The related model name for the
            # networks accessor on system is "network".
            var_name = self._getM2MName(m2model)

            # Simple object to create for our m2m_accessor
            m2m_accessor_model = self._m2m_buildXobjModel(request, m2m_accessor)

            # In django, m2m_accessors are always lists of other models.
            accessorModelValues = []
            setattr(m2m_accessor_model, var_name, accessorModelValues)
            try:
                # For each related model in the m2m_accessor, serialize
                # it, then append the serialized object to the list on
                # m2m_accessor_model.
                accessorValues = [ (x, None)
                    for x in getattr(self, m2m_accessor).all() ]
                for rel_mod, subvalues in accessorValues:
                    rel_mod = rel_mod.serialize(request)
                    accessorModelValues.append(rel_mod)

                setattr(xobj_model, m2m_accessor, m2m_accessor_model)

            # TODO: do we still need to handle this exception here? not
            # sure what was throwing it.
            except exceptions.ObjectDoesNotExist:
                setattr(xobj_model, m2m_accessor, None)

    def _serialize_list_fields(self, xobj_model, request):
        """
        Special handling of list_fields.  For each field in list_fields, get
        the list found at the attribute on the model and serialize each model
        found in that list.  Set a list of the serialized models on
        xobj_model.
        """
        for list_field in self.list_fields:
            listFieldVals = []
            setattr(xobj_model, list_field, listFieldVals)
            show_collapsed = getattr(self, '_supports_collapsed_collection', False)
            for val in getattr(self, list_field, []):
                if hasattr(val, '_meta'):
                    # This is a db model...
                    # now if the collection is marked collapsable mark the kids
                    # as things we need to show in summary view, to
                    if getattr(self, '_supports_collapsed_collection', False):
                        val._summarize = True
                    xobjModelVal = val.serialize(request)
                else:
                    xobjModelVal = val
                listFieldVals.append(xobjModelVal)

    def _serialize_abstract_fields(self, xobj_model, request):
        abstractFields = getattr(self._meta, 'abstract_fields', dict())
        for fieldName, field in abstractFields.iteritems():
            val = getattr(self, fieldName, None)
            if val is None:
                continue
            val = val.serialize(request)
            setattr(xobj_model, fieldName, val)

    def serialize(self, request=None):
        """
        Serialize this model into an object that can be passed blindly into
        xobj to produce the xml that we require.
        """
        # Basic object to use to send to xobj.
        xobjModelClass = self._xobjClass
        xobj_model = xobjModelClass()

        _xobj = getattr(self, '_xobj', None)
        if _xobj:
            xobj_model._xobj = _xobj

        fields = self._get_field_dict()
        m2m_accessors = self._get_m2m_accessor_dict()

        summarize = getattr(self, '_summarize', False)

        self._serialize_fields(xobj_model, fields, request, summarize)
        if not summarize:
            self._serialize_fk_fields(xobj_model, fields, request)
            if self.serialize_accessors:
                accessors = self._get_accessor_dict()
                self._serialize_fk_accessors(xobj_model, accessors, request)
            self._serialize_m2m_accessors(xobj_model, m2m_accessors, request)
            self._serialize_abstract_fields(xobj_model, request)
            self._serialize_list_fields(xobj_model, request)

        return xobj_model

class SyntheticField(object):
    """
    A field that has no database storage, but is de-serialized.
    Can we used to wrap (any?) field type, but defaults to strings.
    Unlike APIReadOnly and Hidden, this is a class, not a function,
    so must do extra work to transfer attributes to the model it wraps.
    """

    def __init__(self, model=None):
        if model is None:
           model = str
        self.model = model
        hidden = getattr(self, 'XObjIdHidden', None)
        ro     = getattr(self, 'APIReadOnly', None)
        if hidden:
             self.model.XObjIdHidden = hidden
        if ro:
             self.model.APIReadOnly  = ro

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
            ret._meta.synthetic_fields = synth = dict()
            ret._meta.abstract_fields = abstr = dict()
            for k, v in attrs.items():
                if isinstance(v, SyntheticField):
                    synth[k] = v.model
                    # Default the value to None
                    setattr(ret, k, None)
                meta = getattr(v, '_meta', None)
                if meta is not None and meta.abstract:
                    abstr[k] = v
                    setattr(ret, k, None)
            return ret

    def serialize(self, request=None):
        xobj_model = XObjModel.serialize(self, request)
        _xobj = getattr(xobj_model, '_xobj', None)
        if _xobj:
            xobj_model._xobj.attributes['id'] = str
        else:
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
                attributes = {})

    def __init__(self, refValue):
        self._xobj.attributes["id"] = str
        setattr(self, "id", refValue)
        
class HrefField(models.Field):
    def __init__(self, href=None, values=None):
        """
        values is an optional tuple of values to be expanded into href
        """
        self.href = href
        self.values = values
        models.Field.__init__(self)

    def serialize_value(self, request=None):
        if request is None:
            return None
        if self.values:
            href = self.href % tuple(self.values)
        else:
            href = self.href
        hrefModel = XObjHrefModel(request.build_absolute_uri(href))
        return hrefModel

class ForeignKey(models.ForeignKey):
    """
    Wrapper of django foreign key for use in models
    """
    def __init__(self, *args, **kwargs):
        # text_field is used when serializing the href.  It is the name of the
        # property to use for node text.  For example, a zone with name zone1
        # serialized as an href would be <zone
        # href="somehost/api/inventory/zones/1"/>.  If you set text_field to
        # be name, it would be <zone
        # href="somehost/api/inventory/zones/1">zone1</zone>.
        if kwargs.has_key('text_field'):
            self.text_field = kwargs['text_field']
            kwargs.pop('text_field')
        else:
            self.text_field = None

        # view_name is the name of the view from urls.py that should be used
        # to build a url for this accessor on the parent model.
        # E.g. Version has a Fk to Project, and the accessor is named
        # versions.  The view_name is ProjectVersions to produce a url like:
        # /api/projects/<short_name>/versions/
        if kwargs.has_key('view_name'):
            self.view_name = kwargs.get('view_name', None)
            kwargs.pop('view_name')
        else:
            self.view_name = None

        super(ForeignKey, self).__init__(*args, **kwargs)

class SerializedForeignKey(ForeignKey):
    """
    By default, Foreign Keys serialize as hrefs on the originating model (the
    model that contains the ForeignKey field). Use this field class if you
    instead want them to serialize to the full xml object representation of
    the target (destination) model.  Be careful of self referenceing models
    that can cause infinite recursion.
    """
    def __init__(self, *args, **kwargs):
        self.text_field = None
        self.serialized = True
        super(SerializedForeignKey, self).__init__(*args, **kwargs)

class DeferredForeignKeyMixIn(object):
    """
    Foreign Key that is deferred.  That means that as we enconter instances of
    this foreign key during serialization, we will create an href for the
    model instead of a full xml representation of the model.
    """
    Deferred = True

class DeferredForeignKey(ForeignKey, DeferredForeignKeyMixIn):
    pass

class DeferredManyToManyField(models.ManyToManyField,
                              DeferredForeignKeyMixIn):
    pass                              

class XMLField(models.TextField):
    """
    django 1.3 deprecated XMLField, but it's still useful for us to mark
    a field as containing XML
    """

class DecimalField(models.DecimalField):
    def to_python(self, value):
        # Django's default is to try to pass a float to decimal.Decimal,
        # and that explodes
        if isinstance(value, float):
            value = str(value)
        return models.DecimalField.to_python(self, value)

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

# Signal for handling synthetic fields being updated
def signalHandler_computeSyntheticFields(sender, instance, **kwargs):
    method = getattr(instance, 'computeSyntheticFields', None)
    if method is not None:
        method(sender, **kwargs)

post_init.connect(signalHandler_computeSyntheticFields)
post_save.connect(signalHandler_computeSyntheticFields)