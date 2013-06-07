#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#

import datetime
from dateutil import parser
import inspect
import urlparse
from lxml import etree
import exceptions as pyexceptions

from conary.lib import util

from django.db import connection, connections
from django.db import models
from django.db.models.base import ModelBase
from django.db.models import fields as djangofields
from django.db.models.fields import related
from django.db.models.signals import post_init, post_save
from django.db.utils import IntegrityError
from django.core import exceptions
from django.core import urlresolvers 

from copy import deepcopy

from mint.django_rest import timeutils
from mint.django_rest.rbuilder import errors
from mint.lib import mintutils
from mint.lib import data as mintdata

class Etree(object):
    @classmethod
    def Node(cls, tag, children=[], attributes={}, text=None, parent=None):
        e = etree.Element(tag)
        # Drop None attributes
        e.attrib.update((k, v) for (k, v) in attributes.iteritems()
                if v is not None)
        e.extend(children)
        e.text = text
        if parent is not None:
            parent.append(e)
        return e

    @classmethod
    def findBasicChild(cls, etreeModel, childName, default=None):
        ret = etreeModel.find(childName)
        if ret is None or len(ret) > 0:
            # If the node has children, its text value is None because
            # we don't support mixed content in our XML
            return default
        if ret.text is None:
            # lxml considers text to be None for <a/> or <a></a> - we
            # expect that to be an empty string, and the absence of the
            # node to be None
            return ''
        return ret.text

    @classmethod
    def findChildren(cls, etreeModel, *path):
        """
        Walk over all the path items, return the last one as a list,
        gracefully handling missing intermediate ones
        """
        return etreeModel.xpath("./%s" % '/'.join(path))

    @classmethod
    def tostring(cls, etreeModel, xmlDeclaration=False, prettyPrint=True,
            encoding="UTF-8", withTail=None):
        if withTail is None:
            withTail = (prettyPrint == True)
        return etree.tostring(etreeModel, xml_declaration=xmlDeclaration,
                pretty_print=prettyPrint, encoding=encoding, with_tail=withTail)

    @classmethod
    def fromstring(cls, strobj):
        return etree.fromstring(strobj)

class BaseFlags(util.Flags):
    __slots__ = []
    __defaults = {}

    def __init__(self, **kwargs):
        # First, compute defaults. Walk mro in reverse order, we may
        # want to override parent defaults
        defaults = {}
        slots = set()
        for cls in reversed(inspect.getmro(self.__class__)):
            defaults.update(getattr(cls, '__defaults__', {}))
            slots.update(getattr(cls, '__slots__', ()))
        for flag in slots:
            value = kwargs.get(flag, defaults.get(flag, False))
            setattr(self, flag, value)

    def __setattr__(self, flag, val):
        # original conary version can only store booleans... logical for a
        # a flags class, but we need more state.  Eventually, make this 
        # class smarter and not rely on it
        object.__setattr__(self, flag, val)

    def copy(self, **kwargs):
        vals = {}
        for cls in inspect.getmro(self.__class__):
            vals.update((flag,  getattr(self, flag))
                for flag in getattr(cls, '__slots__', ()))
        vals.update(kwargs)
        return self.__class__(**vals)

class Flags(BaseFlags):
    __slots__ = [ 'save', 'load', 'original_flags']
    __defaults__ = dict(save=True, load=True, original_flags=None)

# Dict to hold the union of all models' tags as keys, and the model class as
# values.  Needed so that there is exactly one place to look to determine what
# model class to use for deserialization of xml.  All models.py should add
# their models to this dict.
type_map = {}

class etreeObjectWrapper(object):
    def __init__(self, element):
        self.element = element
    def to_xml(self, request=None, etreeModel=None):
        return etree.tostring(self.element, pretty_print=False,
            encoding="UTF-8", xml_declaration=False)

def XObjHidden(field):
    """
    Fields implementing this interface will not be serialized in the
    external API
    """
    field.XObjHidden = True
    return field

def UpdatableKey(field):
    """
    Decorating a field as UpdatableKey will let the requires decorator
    update its value; otherwise, the value specified in the URI will be
    preserved.
    """
    field.UpdatableKey = True
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
    deserialize an object from an etree object into an instance of the model.
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

        if keyFieldVal is not None:
            loadedModels = self.filter(pk=keyFieldVal)
        elif model_inst.load_fields:   
            loadedModels = self.filter(**model_inst._load_fields_dict())
        else:
            return None, None
        if len(loadedModels) != 1:
            return None, None
        oldModel = loadedModels[0].serialize()
        return oldModel, loadedModels[0]

    def _load(self, model_inst, etreeModel, withReadOnly=False):
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

        # First try to load by an id or href attribute on etreeModel.  This
        # attribute (if present) should a be the full url of the model.
        loadedModel = self._load_from_href(etreeModel)
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
            self._copyFields(loadedModel, model_inst, etreeModel,
                withReadOnly=withReadOnly)
            return oldModel, loadedModel

        if withReadOnly:
            # Don't touch the old model's fields even if they are read-only
            return oldModel, loadedModel

        # We need to remove the read-only fields, added from the etree model
        for field in model_inst._meta.fields:
            if getattr(field, 'APIReadOnly', None):
                defaultValue = None
                if not field.null and isinstance(field, djangofields.BooleanField):
                    defaultValue = field.default
                setattr(model_inst, field.name, defaultValue)
        return oldModel, loadedModel

    def _copyFields(self, dest, src, etreeModel=None, withReadOnly=False):
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
            # provided on etreeModel.
            if newFieldVal is None and (etreeModel is None or etreeModel.find(field.name) is None):
                continue

            # Set the new value on dest if it differs from the old value.
            oldFieldVal = getattr(dest, field.name)
            if newFieldVal != oldFieldVal:
                setattr(dest, field.name, newFieldVal)

    def load_or_create(self, model_inst, etreeModel=None, withReadOnly=False):
        """
        Similar in vein to django's get_or_create API.  Try to load a model
        based on model_inst, if one wasn't found, create one and return it.
        """
        # Load the model from the db.
        oldModel, loaded_model = self._load(model_inst,
            etreeModel=etreeModel, withReadOnly=withReadOnly)
        if not loaded_model:
            # No matching model was found. We need to save.  This scenario
            # means we must be creating something new (POST), so it's safe to
            # go ahead and save here, if something goes wrong later, this will
            # be automatically rolled back.
            model_inst.save()
            loaded_model = model_inst

        return oldModel, loaded_model

    def _load_from_href(self, etreeModel):
        """
        Given an etreeModel, and an attribute to look at on that etreeModel for
        a url, try to load the corresponding django model identified by that
        url.
        """

        if etreeModel is None:
            return None

        # Check both href and id, preferring id.
        for propName in [ 'id', 'href' ]:
            href = etreeModel.attrib.get(propName)
            if href is not None:
                break
            href = etreeModel.find(propName)
            if href is not None:
                href = href.text
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

    def lock(self):
        """Lock table."""
        if 'sqlite' in connections[self.db].settings_dict['ENGINE'].lower():
            return
        cursor = connection.cursor()
        cursor.execute("LOCK TABLE %s" % self.model._meta.db_table)

    @classmethod
    def _etreeGetProperty(cls, etreeModel, model, field):
        if isinstance(field, basestring):
            fieldName = field
        else:
            fieldName = field.name
        # If the field is defined as an attribute, prefer attributes
        # over elements
        if fieldName in model._xobj.attributes:
            ret = etreeModel.attrib.get(fieldName)
            if ret is not None:
                return ret
            # Look for an element too
            val = etreeModel.find(fieldName)
            return val
        # Not an attribute. Prefer elements
        val = etreeModel.find(fieldName)
        if val is not None:
            return val
        return etreeModel.attrib.get(fieldName)

    def _add_fields(self, model, etreeModel, request, flags=None):
        """
        For each etreeModel attribute, if the attribute matches a field name on
        model, set the attribute's value on model.
        """
        fields = model._get_field_dict()
        set_fields = set([])

        for field in fields.values():
            fieldName = field.name
            # special case for fields that may not exist at load time or we
            # want to ignore for other reasons
            if fieldName in model.load_ignore_fields:
                continue
            val = self._etreeGetProperty(etreeModel, model, field)
            if val is None:
                continue
            # If val is an empty string, and it has no elements and no
            # attributes, then it's not a complex xml element, so the intent
            # is to set the new value to None on the model.
            if not val.text and not val.attrib and not val.getchildren():
                val = None
            # Serialized foreign keys are serialized inline, so we need to
            # load the model for them based on their inline xml
            # representation.
            elif isinstance(field, SerializedForeignKey):
                val = field.related.parent_model.objects.load_from_object(val,
                        request, flags=flags)

            # Foreign keys can be serialized based on a text field, or the
            # text of an xml elements, try to load the foreign key model if
            # so.
            elif isinstance(field, ForeignKey) and \
                 field.text_field is not None and \
                 not val.getchildren() and val.text:
                lookup = { field.text_field : val.text }
                # Look up the inlined value
                val = field.related.parent_model.objects.get(**lookup)

            # Handle other related fields that could be inlined.
            elif isinstance(field, related.RelatedField):
                parentModel = field.rel.to
                val = parentModel.objects.load_from_object(val, request,
                        flags=flags)

            # Handle different combinations of true/True, etc for
            # BooleanFields.
            elif isinstance(field, (djangofields.BooleanField,
                                    djangofields.NullBooleanField)):
                # val may have been an attribute
                val = getattr(val, 'text', val)
                val = (val.lower() == 'true')

            # Handle xml fields
            elif isinstance(field, XMLField):
                # Grab the first child, rename it as the main field
                for subelement in val.iterchildren():
                    val = etree.tostring(subelement, pretty_print=False, xml_declaration=False)
                    break
                else:
                    val = None

            # DateTimeUtcFeilds can not be set to empty string.
            elif isinstance(field, DateTimeUtcField):
                val = getattr(val, 'text', val)

            # All other cases where val was specified, use Django's
            # get_prep_value, except in the case of the primary key.
            elif val is not None:
                if field.primary_key:
                    try:
                        val = int(val.text)
                    except:
                        # primary keys might not just be ints!
                        val = val.text
                else:
                    # Cast to str, django will just do the right thing.
                    val = getattr(val, 'text', val)
                    val = field.get_prep_value(val)

            else:
                val = None

            set_fields.add(field.name)
            setattr(model, field.name, val)

        # Values for fields that are not provided should be preserved.
        # However, since we've instantiated the model, we've gotten the
        # default values for all fields.  Make sure those default values don't
        # get saved, overwriting existing values if they weren't actually
        # provided.
        for field in model._meta.fields:
            if field.name in set_fields:
                continue
            try:
                value = getattr(model, field.name, None)
            except exceptions.ObjectDoesNotExist:
                continue
            if value is None:
                continue
            # There is a value, and we didn't set the field, so it wasn't
            # provided.
            default_val = field.get_default()
            if default_val != '':
                continue
            setattr(model, field.name, None)

        return model

    def _add_list_fields(self, model, etreeModel, request, flags=None):
        """
        For each list_field on the model, get the objects off of etreeModel, load
        their corresponding model and add them to our model in a list.
        """
        for key in model.list_fields:
            flist = etreeModel.iterchildren(key)

            mods = []
            for val in flist:
                m = type_map[key].objects.load_from_object(val, request,
                    flags=flags)
                mods.append(m)
            if mods:
                setattr(model, key, mods)

        return model

    def _get_accessors(self, model, etreeModel, request=None, flags=None):
        """
        Build and return a dict of accessor name and list of accessor
        objects.
        """
        accessors = model._get_accessor_dict()
        ret_accessors = {}

        # We're creating related models, such as a network model
        # that's going to reference a system, well since system is
        # not yet set as  FK, we can't save the network model yet,
        # so pass False for the save flag.
        #
        # BUT: in doing so, we forgot our original intent, and in some
        # cases we need this behavior... unfortuantely... really we need
        # to make loading just use the xobj models as much as possible
        # as requiring many2many relationships to pre-exist is complicated
        # (original_flags is largely for this purpose, see below)
        flags = Flags(save=False, original_flags=flags)

        for accessorName, accessor in accessors.items():
            val = etreeModel.find(accessorName)
            if val is None:
                continue
            ret_accessors[accessorName] = accessorList = []
            rel_obj_model = accessor.model
            rel_obj_name = rel_obj_model.getTag()
            rel_objs = list(val.iterchildren(rel_obj_name))
            if rel_objs is None:
                continue
            for rel_obj in rel_objs:
                rel_mod = type_map[rel_obj_name].objects.load_from_object(
                    rel_obj, request, flags=flags)
                accessorList.append(rel_mod)
        return ret_accessors

    def _add_accessors(self, model, accessors):
        """
        For each model attribute, if the attribute matches an accessor name,
        load all the acccessor models off model and add them to the model's 
        accessor.
        """
        for key, val in accessors.items():
            for v in val:
                getattr(model, key).add(v)
        return model

    def _set_m2m_accessor(self, model, m2m_accessor, rel_mod, flags=None):
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

    def _add_m2m_accessors(self, model, etreeModel, request, flags=None):
        """
        Populate the many to many accessors on model based on the etree model
        in etreeModel.
        """
        flags = flags.copy(save=False, original_flags=flags)
        for m2m_accessor, m2m_mgr in model._get_m2m_accessor_dict().items():
            _xobj = getattr(m2m_mgr.model, '_xobj', None)
            if _xobj:
                rel_obj_name = _xobj.tag or m2m_mgr.target_field_name
            else:
                rel_obj_name = m2m_mgr.target_field_name

            acobj = etreeModel.find(m2m_accessor)
            if acobj is None:
                continue
            objlist = list(acobj.iterchildren(rel_obj_name))
            if objlist:
                self._clear_m2m_accessor(model, m2m_accessor)
            for rel_obj in objlist or []:
                modelCls = m2m_mgr.model
                rel_mod = modelCls.objects._load_from_href(rel_obj)
                if rel_mod is None:
                    rel_mod = modelCls.objects.load_from_object(
                        rel_obj, request, flags=flags)
                self._set_m2m_accessor(model, m2m_accessor, rel_mod, flags=flags)

        return model

    def _add_synthetic_fields(self, model, etreeModel, request):
        # Not all models have the synthetic fields option set, so use getattr
        for fieldName, fmodel in getattr(model._meta, 'synthetic_fields', {}).items():
            if fmodel.APIReadOnly:
                continue
            # Since this is a field, we ignore all but the first
            # occurrence
            val = etreeModel.find(fieldName)
            if val is None:
                continue
            modelClass = fmodel.model
            if modelClass is str:
                val = val.text
            elif isinstance(modelClass, XObjIdModel):
                raise Exception("Unexpected serialization object")
            elif inspect.isclass(modelClass):
                if issubclass(modelClass, XObjModel):
                    val = modelClass.objects.load_from_object(val, request)
                elif not issubclass(modelClass, EtreeField):
                    raise Exception("Unexpected serialization object")
            if val is not None:
                setattr(model, fieldName, val)
        return model

    def _add_abstract_fields(self, model, etreeModel):
        abstractFields = getattr(model._meta, 'abstract_fields', None)
        if not abstractFields:
            return model
        for fieldName, mdl in abstractFields.items():
            val = etreeModel.find(fieldName)
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


    def load_from_object(self, etreeModel, request, flags=None):
        """
        Given an object (etreeModel) , create and return the  corresponding
        model.  If load is True, load the model from the db and apply the
        updates to it based on etreeModel, otherwise, always create a new model.
        """
        if flags is None:
            flags = Flags(save=True, load=True)

        # Every manager has access to the model it's a manager for, create an
        # empty model instance to start with.
        model = self.model()

        origFlags = flags

        # Don't even attempt to save abstract models
        if model._meta.abstract:
            flags = flags.copy(save=False)

        # We need access to synthetic fields before loading from the DB, they
        # may be used in load_or_create
        model = self._add_synthetic_fields(model, etreeModel, request)
        model = self._add_fields(model, etreeModel, request, flags=flags)
        accessors = self._get_accessors(model, etreeModel, request, flags=flags)

        # Only try to load the model if load is True.  
        if not flags.load:
            try:
                model.save()
            except IntegrityError, e:
                e.status = errors.BAD_REQUEST
                raise e
            oldModel = None
        elif flags.save:
            oldModel, model = self.load_or_create(model, etreeModel)
        else:
            oldModel, dbmodel = self._load(model, etreeModel)
            if dbmodel:
                model = dbmodel

        model = self._add_synthetic_fields(model, etreeModel, request)

        # If this is an abstract model, we want to pass down the
        # original flags, because we've turned saving off here.
        model = self._add_m2m_accessors(model, etreeModel, request, flags=flags)
        model = self._add_list_fields(model, etreeModel, request, flags=origFlags)
        model = self._add_accessors(model, accessors)
        model = self._add_abstract_fields(model, etreeModel)

        # Save a reference to the oldModel on model.  This could be helpful
        # later on to detect state changes.
        model.oldModel = oldModel
        # Save a reference to the original etree model, e.g. to inspect
        # read-only fields
        model._etreeModel = etreeModel

        return model

class PackageJobManager(BaseManager):

    def _add_fields(self, model, obj, request, flags=None):
        job_data = getattr(obj, "job_data", None)
        
        if job_data is not None:
            obj.__dict__.pop("job_data")
            job_data_dict = {}
            for k, v in job_data.__dict__.items():
                if not k.startswith("_"):
                    job_data_dict[k] = v
            marshalled_job_data = mintdata.marshalGenericData(job_data_dict) 
            model.job_data = marshalled_job_data

        return BaseManager._add_fields(self, model, obj, request, flags=flags)

class TroveManager(BaseManager):
    def load_from_object(self, obj, request, flags=None):
        # None flavor fixup
        if getattr(obj, 'flavor', None) is None:
            obj.flavor = ''
        # Fix up the flavor in the version object
        obj.version.flavor = obj.flavor
        return BaseManager.load_from_object(self, obj, request, flags=flags)

    def _clear_m2m_accessor(self, model, m2m_accessor):
        # We don't want available_updates to be published via REST
        if m2m_accessor == 'available_updates':
            return
        BaseManager._clear_m2m_accessor(self, model, m2m_accessor)

    def _set_m2m_accessor(self, model, m2m_accessor, rel_mod, flags=None):
        if m2m_accessor == 'available_updates':
            return
        return BaseManager._set_m2m_accessor(self, model, m2m_accessor, rel_mod, flags=flags)

    def _add_fields(self, model, obj, request, flags=None):
        nmodel = BaseManager._add_fields(self, model, obj, request, flags=flags)
        if nmodel.flavor is None:
            nmodel.flavor = ''
        return nmodel

    def _load_from_href(self, *args, **kwargs):
        return None

class SaveableManyToManyManager(BaseManager):

    # our many to many handling needs some help, in the case where we want
    # to make new relations, some may have IDs and some may not, and we
    # must precreate ones that don't so we can add them, but we never
    # want to do this on load if our intent is not to save at the end for
    # security reasons, because GETs have a different set of permissions and
    # users could be destructive.

    def _set_m2m_accessor(self, model, m2m_accessor, rel_mod, flags=None):
        accessor = getattr(model, m2m_accessor)
        try:
            accessor.add(rel_mod)
        except pyexceptions.ValueError:
            if flags and flags.original_flags and flags.original_flags.save: 
                if not (m2m_accessor in model._m2m_safe_to_create):
                    raise Exception("unable to save %s" % m2m_accessor)
                rel_mod.save()
                accessor.add(rel_mod)


class VersionManager(BaseManager):
    def _add_fields(self, model, obj, request, flags=None):
        # Fix up label and revision
        nmodel = BaseManager._add_fields(self, model, obj, request, flags=flags)
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
    def load_from_object(self, obj, request, flags=None):
        model = self.model(system=None)
        # XXX This doesn't really sound right -- misa
        for k, v in obj.attrib.iteritems():
            setattr(model, k, v)
        for child in obj.iterchildren():
            setattr(model, child.tag, child.text)
        return model

class ConfigurationDescriptorManager(CredentialsManager):
    pass

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
        if m2m_accessor in [ 'jobs' ]:
            return
        BaseManager._clear_m2m_accessor(self, model, m2m_accessor)

    def _set_m2m_accessor(self, model, m2m_accessor, rel_mod, flags=None):
        # XXX Need a better way to handle this
        if m2m_accessor == 'jobs':
            self._handleSystemJob(model, rel_mod)
        else:
            BaseManager._set_m2m_accessor(self, model, m2m_accessor, rel_mod, flags=flags)

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
        job.time_updated = timeutils.now()
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
                model.updateNetworks(val)
                continue
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
        Overridden because collections have no direct representation in the db - 
        we need to load individual objects
        """
        model = self.model()
        return None, model

class RbacRolesManager(StubManager):
    pass

class RbacContextsManager(StubManager):
    pass

class RbacPermissionsManager(StubManager):
    pass

class RbacPermissionTypesManager(StubManager):
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

class SyntheticField(object):
    """
    A field that has no database storage, but is de-serialized.
    Can we used to wrap (any?) field type, but defaults to strings.
    Unlike APIReadOnly and Hidden, this is a class, not a function,
    so must do extra work to transfer attributes to the model it wraps.
    """

    __slots__ = ['model', 'XObjHidden', 'APIReadOnly', 'docstring',
        'shortname', ]

    def __init__(self, model=None):
        self.XObjHidden = False
        self.APIReadOnly = False
        self.docstring = ''
        self.shortname = ''
        if model is None:
            model = str
        self.model = model

class EtreeField(object):
    pass

class XObjModel(models.Model):
    """
    Common model class all models should inherit from.  Overrides the default
    manager on a model with our BaseManager.  Implements get_absolute_url on
    all models.  Adds ability to serialize a model to xml using xobj.
    """
    class __metaclass__(ModelBase):
        """
        Metaclass for all models.  
        Sets the _xobjClass attribute on the class, and consolidates _xobj
        metadata across all base classes.  Such that attributes/elements in _xobj
        specified on base classes are consolidated in the subclass as opposed to
        overwritten.
        """
        def __new__(cls, name, bases, attrs):
            ret = ModelBase.__new__(cls, name, bases, attrs)
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

            ret._meta.synthetic_fields = synth = dict()
            ret._meta.abstract_fields = abstr = dict()
            # Inherit abstract and synthetic fields from the base class
            for bc in bases:
                meta = getattr(bc, '_meta', None)
                if meta is None:
                    continue
                synth.update(getattr(meta, 'synthetic_fields', {}))
                abstr.update(getattr(meta, 'abstract_fields', {}))

            for k, v in attrs.items():
                if isinstance(v, SyntheticField):
                    synth[k] = v
                    # Default the value to None
                    setattr(ret, k, None)
                meta = getattr(v, '_meta', None)
                if meta is not None and meta.abstract:
                    abstr[k] = v
                    setattr(ret, k, None)
            return ret

    class Meta:
        abstract = True

    # The manager gets set by the service when it dispatches one of the
    # HTTP methods.
    # Don't expect _rbmgr to be set when loading fixtures, for instance
    _rbmgr = None

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

    def _load_fields_dict(self):
        """
        Returns a dict of field name, field value for each field in
        load_fields.
        """
        fields_dict = {}
        for f in self.load_fields:
            fields_dict[f.name] = getattr(self, f.name, None)
        return fields_dict

    def to_xml(self, request=None, etreeModel=None):
        """
        Returns the xml serialization of this model.
        """
        if not etreeModel:
            etreeModel = self.serialize(request)
        return etree.tostring(etreeModel, pretty_print=True,
                encoding="UTF-8", xml_declaration=True)

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
        if not isinstance(self.url_key, list):
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

    def _serialize_fields(self, etreeModel, fields, request, summarize):
        """
        For each attribute on self (the model), see if it's a field, if so,
        set the value on etreeModel.  Then, remove it from fields, as don't
        want to try to serialize it later.
        """
        syntheticFields = getattr(self._meta, 'synthetic_fields', {})
        for key, val in self.__dict__.items():
            field = fields.pop(key, None)
            if field is None:
                field = syntheticFields.get(key)
                if field is not None:
                    if getattr(field, 'XObjHidden', False):
                        continue
                    if inspect.isclass(field.model) and issubclass(field.model, EtreeField):
                        if isinstance(val, etree._Element):
                            etreeModel.append(val)
                            continue

                    # XXX using isinstance seems bad. We should make sure
                    # val is an acceptable value for a field, and that can
                    # be any field, model or xobj object, and it's hard
                    if (val is not None and not isinstance(val, (int, bool))):
                        # The user specified a value for the synthetic field.
                        # We'll use that instead of the one from the class def
                        field = val
                    else:
                        field = field.model
            if field is not None:
                if getattr(field, 'XObjHidden', False):
                    continue
                if val is None:
                    val = ''
                elif hasattr(field, 'to_xobj'):
                    val = field.to_xobj(val, request)
                # Special handling of DateTimeFields.  Could make this OO by
                # calling .seriaize(...) on each field, and overriding that
                # behavior for DateTimeField's, but as long as it's just this
                # one case, we'll leave it like this.
                elif isinstance(field, models.DateTimeField):
                    val = val.replace(tzinfo=timeutils.TZUTC)
                    val = val.isoformat()
                elif isinstance(field, (djangofields.BooleanField,
                                        djangofields.NullBooleanField)):
                    val = str(bool(val)).lower()
                elif isinstance(field, XMLField):
                    if val is None or val == '':
                        continue
                    val = etree.fromstring(val)
                    etreeModel.append(Etree.Node(field.name, children=[val]))
                    continue
                elif isinstance(field, HrefField):
                    if isinstance(val, HrefField):
                        # If a value was passed in, then ignore the
                        # definition and use the value
                        field = val
                    etreeModel.append(field.serialize_value(request, tag=key))
                    continue
                elif isinstance(field, djangofields.DecimalField):
                    val = str(float(val))
                elif isinstance(val, XObjModel):
                    # allow nested synthetic fields to override serialization
                    # if the child of the synthetic field is an XObjIdModel
                    etreeModel.append(val.serialize(request, tag=key))
                    continue
                elif hasattr(val, "getElementTree"):
                    val = val.getElementTree().element
                    etreeModel.append(val)
                    continue

                _xobj = getattr(self, '_xobj', None)
                if _xobj and key in _xobj.attributes:
                    etreeModel.attrib[key] = unicode(val)
                else:
                    Etree.Node(tag=key, parent=etreeModel, text=unicode(val))
  
    def _serialize_fk_fields(self, etreeModel, fields, request):
        """
        For each remaining field in fields, see if it's a FK field, if so set
        the create an href object and set it on etreeModel.
        TODO: accessors?
        """
        for fieldName in fields:
            field = fields[fieldName]
            if getattr(field, 'XObjHidden', False):
                continue
            if not isinstance(field, related.RelatedField):
                continue
            val = getattr(self, fieldName)
            text_field = getattr(field, 'text_field', None)
            serialized = getattr(field, 'serialized', False)
            visible = getattr(field, 'visible', None)
            if not val:
                # Create empty node
                Etree.Node(fieldName, parent=etreeModel)
                continue
            if visible:
                # If the visible prop is set, we want to copy the
                # field's value for that property
                etreeModel.append(val.serialize(request, tag=fieldName))
                continue
            if serialized:
                serialized_as = getattr(val, 'serialized_as', fieldName)
                val = val.serialize(request, tag=serialized_as)
                etreeModel.append(val)
                continue

            absolute_url = val.get_absolute_url(request)
            refModel = Etree.Node(fieldName, attributes=dict(id=absolute_url),
                    parent=etreeModel)
            if hasattr(val, "summary_view") and fieldName not in getattr(self, '_xobj_summary_view_hide', []):
                for sField in val.summary_view:
                    try:
                        sVal = getattr(val, sField, None)
                        Etree.Node(sField, text=sVal, parent=refModel)
                    except:
                        # if summary view references value that doesn't exist
                        pass
            else:
                if text_field:
                    textValue = getattr(val, text_field)
                    if textValue:
                        refModel.text = textValue

    def _serialize_fk_accessors(self, etreeModel, accessors, request):
        """
        Builds up an object for each accessor for this model and sets it on
        etreeModel.  This is so that things like <networks> appear as an xml
        representation on <system> xml.
        """
        xobjExplicitAccessors = getattr(self, '_xobj_explicit_accessors', None)
        if xobjExplicitAccessors is not None:
            accessorsList = [ (k, v) for (k, v) in accessors.items()
                if k in xobjExplicitAccessors ]
        else:
            blacklist =  getattr(self, '_xobj_hidden_accessors', set())
            accessorsList = [ (k, v) for (k, v) in accessors.items()
                if k not in blacklist ]

        for accessorName, accessor in accessorsList:
            # Look up the name of the related model for the accessor.  Can be
            # overriden via _xobj.  E.g., The related model name for the
            # networks accessor on system is "network".
            var_name = self.getAccessorName(accessor)

            accessorEtreeModel = Etree.Node(accessorName, parent=etreeModel)
            if getattr(accessor.field, 'Deferred', False):

                # The accessor is deferred.  Create an href object for it
                # instead of a object representing the xml.
                rel_mod = accessor.model()
                viewName = accessor.field.relatedViewName
                if viewName:
                    href = self.get_absolute_url(request, view_name=viewName)
                else:
                    href = rel_mod.get_absolute_url(request, parents=[self],
                        view_name=accessor.field.view_name)
                if href:
                    accessorEtreeModel.attrib['id'] = href
                continue

            try:
                # For each related model in the accessor, serialize it,
                # then append the serialized object to the list
                accessorValues = getattr(self, accessorName)
                if isinstance(accessorValues, BaseManager):
                    accessorValues = [ (x, None)
                        for x in accessorValues.all() ]
                else:
                    accessorValues = None
                if accessorValues is not None:
                    for rel_mod, subvalues in accessorValues:
                        rel_mod_ser = rel_mod.serialize(request, tag=var_name)
                        accessorEtreeModel.append(rel_mod_ser)
                        if 'id' in rel_mod_ser.attrib:
                            continue

                        # attempt to add IDs where known to reverse
                        # FK relationships (aka one-to-many)
                        view_name = getattr(rel_mod, 'view_name', None)

                        if view_name is None:
                            continue
                        href = rel_mod.get_absolute_url(request,
                            parents=[self],
                            view_name=rel_mod.view_name)
                        if href:
                            rel_mod_ser.attrib['id'] = href
            # TODO: do we still need to handle this exception here? not
            # sure what was throwing it.
            except exceptions.ObjectDoesNotExist:
                raise

    def _m2m_buildEtreeModel(self, request, m2mAccessorName):
        dmodel = type_map.get(m2mAccessorName)
        etreeModel = Etree.Node(m2mAccessorName)
        if dmodel is not None:
            _xobj = getattr(dmodel, '_xobj', None)
            if _xobj is not None:
                if 'id' in _xobj.attributes:
                    m = dmodel()
                    m2mId = m.get_absolute_url(request, parents=[self])
                    if m2mId:
                        etreeModel.attrib['id'] = m2mId
        return etreeModel

    def _serialize_m2m_accessors(self, etreeModel, m2m_accessors, request):
        """
        Build up an object for each many to many field on this model and set
        it on etreeModel.
        """
        m2mWhitelist = getattr(self, '_xobj_explicit_m2m', None)
        m2mBlacklist = getattr(self, '_xobj_hidden_m2m', [])
        for m2m_accessor in m2m_accessors:
            if m2mWhitelist is not None and m2m_accessor not in m2mWhitelist:
                continue
            if m2m_accessor in m2mBlacklist:
                continue
            deferred = getattr(self._meta.get_field(m2m_accessor), 
                "Deferred", None)
            if deferred:
                rel_mod = type_map[m2m_accessor]()
                resourceId = rel_mod.get_absolute_url(request, parents=[self])
                Etree.Node(m2m_accessor, attributes=dict(id=resourceId), parent=etreeModel)
                continue

            m2model = m2m_accessors[m2m_accessor].model
            # Look up the name of the related model for the accessor.  Can be
            # overriden via _xobj.  E.g., The related model name for the
            # networks accessor on system is "network".
            var_name = self._getM2MName(m2model)

            # Simple object to create for our m2m_accessor
            m2mEtreeModel = self._m2m_buildEtreeModel(request, m2m_accessor)
            etreeModel.append(m2mEtreeModel)
            try:
                # For each related model in the m2m_accessor, serialize
                # it, then append the serialized object to the list
                accessorValues = [ (x, None)
                    for x in getattr(self, m2m_accessor).all() ]
                for rel_mod, subvalues in accessorValues:
                    rel_mod = rel_mod.serialize(request, tag=var_name)
                    m2mEtreeModel.append(rel_mod)
            # TODO: do we still need to handle this exception here? not
            # sure what was throwing it.
            except exceptions.ObjectDoesNotExist:
                raise

    def _serialize_list_fields(self, etreeModel, request):
        """
        Special handling of list_fields.  For each field in list_fields, get
        the list found at the attribute on the model and serialize each model
        found in that list.  Set a list of the serialized models on
        etreeModel.
        """
        for list_field in self.list_fields:
            show_collapsed = getattr(self, '_supports_collapsed_collection', False)
            for val in getattr(self, list_field, []):
                if hasattr(val, '_meta'):
                    # This is a db model...
                    # now if the collection is marked collapsable mark the kids
                    # as things we need to show in summary view, to
                    if getattr(self, '_supports_collapsed_collection', False):
                        val._summarize = True
                    xobjModelVal = val.serialize(request, tag=list_field)
                elif isinstance(val, HrefField):
                    tag = list_field
                    # We do have mixed lists like JobResults, so let the
                    # tag be variable
                    if val.tag is not None:
                        tag = val.tag
                    xobjModelVal = val.serialize_value(request, tag=tag)
                else:
                    xobjModelVal = val
                etreeModel.append(xobjModelVal)

    def _serialize_abstract_fields(self, etreeModel, request):
        abstractFields = getattr(self._meta, 'abstract_fields', dict())
        for fieldName, field in abstractFields.iteritems():
            val = getattr(self, fieldName, None)
            if val is None:
                continue
            val = val.serialize(request, tag=fieldName)
            etreeModel.append(val)

    def serialize(self, request=None, tag=None):
        """
        Serialize this model into an object that can be passed blindly into
        xobj to produce the xml that we require.
        """

        if tag is None:
            _xobj = getattr(self, '_xobj', None)
            if _xobj:
                tag = _xobj.tag
        if tag is None:
            raise Exception("Tag not specified for object %s" % self)

        etreeModel = Etree.Node(tag)

        fields = self._get_field_dict()
        m2m_accessors = self._get_m2m_accessor_dict()

        summarize = getattr(self, '_summarize', False)

        self._serialize_fields(etreeModel, fields, request, summarize)
        if not summarize:
            self._serialize_fk_fields(etreeModel, fields, request)
            if self.serialize_accessors:
                accessors = self._get_accessor_dict()
                self._serialize_fk_accessors(etreeModel, accessors, request)
            self._serialize_m2m_accessors(etreeModel, m2m_accessors, request)
            self._serialize_abstract_fields(etreeModel, request)
            self._serialize_list_fields(etreeModel, request)

        return etreeModel

    def update(self, **kwargs):
        """
        Directly update the fields specified in kwargs, updating the current
        object too
        """
        self.__class__.objects.filter(pk=self.pk).update(**kwargs)
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

class XObjIdModel(XObjModel):
    """
    Model that sets an id attribute on itself corresponding to the href for
    this model.
    """
    class Meta:
        abstract = True

    def serialize(self, request=None, tag=None):
        etreeModel = XObjModel.serialize(self, request, tag=tag)
        objId = self.get_absolute_url(request)
        if objId is not None:
            etreeModel.attrib['id'] = objId
        return etreeModel

class XObjHrefModel(object):
    """
    Model that serializes to an href.
    """
    def __init__(self, refValue):
        self.attributes = dict(id=refValue)

class AbsoluteHref(object):
    def __init__(self, relativeHref):
        self.href = relativeHref

    def serialize(self, request):
        return request.build_absolute_uri(self.href)

class HrefField(models.Field):
    def __init__(self, href=None, values=None):
        """
        values is an optional tuple of values to be expanded into href
        """
        self.href = href
        self.values = values
        models.Field.__init__(self)

    def _getRelativeHref(self, url=None):
        if self.values:
            href = self.href % tuple(self.values)
        else:
            href = self.href
        if url is None:
            return href
        if href is None:
            return url
        return "%s/%s" % (url, href)

    def serialize_value(self, request=None, tag=None):
        href = self._getRelativeHref()
        if request is not None:
            href = request.build_absolute_uri(href)
        attributes = {}
        if href is not None:
            attributes.update(id=href)
        et = Etree.Node(tag, attributes=attributes)
        return et

class HrefFieldFromModel(HrefField):
    """
    Build an href out of another model
    """
    def __init__(self, model=None, viewName=None, tag=None):
        self.model = model
        self.viewName = viewName
        if tag is None:
            if model is not None:
                tag = self.model._xobj.tag
        self.tag = tag
        HrefField.__init__(self)

    def serialize_value(self, request=None, tag=None):
        "Extracts the URL from the given model and builds an href from it"
        if self.model is None:
            url = urlresolvers.reverse(self.viewName)
            url = request.build_absolute_uri(url)
        else:
            # FIXME: why is this hack required? something is returning something
            # wrong up the chain
            if type(self.model) == list:
                self.model = self.model[0]
            url = self.model.get_absolute_url(request, view_name=self.viewName)

        url = self._getRelativeHref(url=url)
        if tag is None:
            tag = self.tag
        et = Etree.Node(tag, attributes=dict(id=url))
        return et

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
        self.serialized_as = kwargs.pop('serialized_as', None)
        super(SerializedForeignKey, self).__init__(*args, **kwargs)

class DeferredForeignKeyMixIn(object):
    """
    Foreign Key that is deferred.  That means that as we enconter instances of
    this foreign key during serialization, we will create an href for the
    model instead of a full xml representation of the model.
    """
    Deferred = True
    def setRelatedViewName(self, viewName):
        self.relatedViewName = viewName

class DeferredForeignKey(DeferredForeignKeyMixIn, ForeignKey):
    def __init__(self, *args, **kwargs):
        relatedViewName = kwargs.pop('related_view_name', None)
        ForeignKey.__init__(self, *args, **kwargs)
        self.setRelatedViewName(relatedViewName)

class DeferredManyToManyField(DeferredForeignKeyMixIn, models.ManyToManyField):
    def __init__(self, *args, **kwargs):
        relatedViewName = kwargs.pop('related_view_name', None)
        models.ManyToManyField.__init__(self, *args, **kwargs)
        self.setRelatedViewName(relatedViewName)

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


class DecimalTimestampField(DecimalField):

    def __init__(self, **kwargs):
        kwargs.setdefault('max_digits', 14)
        kwargs.setdefault('decimal_places', 3)
        DecimalField.__init__(self, **kwargs)

    def to_xobj(self, val, request):
        if val is not None and val != 0:
            ts = timeutils.fromtimestamp(val)
            return ts.isoformat()
        else:
            return ''


class DateTimeUtcField(models.DateTimeField):
    """
    Like a DateTimeField, but default to using a datetime value that is set to
    utc time and utc time zone for default values.
    """
    def pre_save(self, model_instance, add):
        if self.auto_now or (self.auto_now_add and add):
            value = timeutils.now()
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
            return prep_value.replace(tzinfo=timeutils.TZUTC)
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
            return python_value.replace(tzinfo=timeutils.TZUTC)
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
        keyName, keyValue = kwargs.items()[0]
        try:
            return cls._get(modelClass, keyName, keyValue)
        except modelClass.DoesNotExist:
            # Try again, after we invalidate the cache
            cls._cache.pop(modelClass, None)
            return cls._get(modelClass, keyName, keyValue)

    @classmethod
    def _get(cls, modelClass, keyName, keyValue):
        cached = cls._getCachedClass(modelClass)
        try:
            return cached.get(keyName, keyValue)
        except KeyError:
            raise modelClass.DoesNotExist()

    @classmethod
    def all(cls, modelClass):
        return cls._getCachedClass(modelClass).all()

    @classmethod
    def reset(cls):
        cls._cache.clear()

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
