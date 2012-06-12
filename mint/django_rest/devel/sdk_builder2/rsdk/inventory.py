from rsdk.Fields import *  # pyflakes=ignore
from rsdk.sdk import SDKModel, register, DynamicImportResolver  # pyflakes=ignore
from xobj2.xobj2 import XObj, XObjMetadata, Field  # pyflakes=ignore

REGISTRY = {}

@register
class Targets(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'targets',
        elements = [
            Field('targettype', CharField),
            Field('targetname', CharField),
            Field('targetid', IntegerField)
        ],
        attributes = dict(
    
        ),
    )

@register
class SystemType(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'system_type',
        elements = [
            Field('infrastructure', BooleanField),
            Field('name', CharField),
            Field('creation_descriptor', XMLField),
            Field('created_date', DateTimeUtcField),
            Field('system_type_id', AutoField),
            Field('description', CharField)
        ],
        attributes = dict(
            id=str
        ),
    )

@register
class JobState(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'job_state',
        elements = [
            Field('job_state_id', AutoField),
            Field('name', CharField)
        ],
        attributes = dict(
            id=str
        ),
    )

@register
class Configuration(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'configuration',
        elements = [
    
        ],
        attributes = dict(
            id=str
        ),
    )

@register
class Credentials(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'credentials',
        elements = [
    
        ],
        attributes = dict(
            id=str
        ),
    )

@register
class Job(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'job',
        elements = [
            Field('time_updated', DateTimeUtcField),
            Field('job_id', AutoField),
            Field('status_code', IntegerField),
            Field('job_state', InlinedDeferredForeignKey),
            Field('time_created', DateTimeUtcField),
            Field('status_detail', TextField),
            Field('status_text', TextField),
            Field('job_uuid', CharField),
            Field('event_type', InlinedForeignKey)
        ],
        attributes = dict(
            id=str
        ),
    )

@register
class ManagementInterface(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'management_interface',
        elements = [
            Field('name', CharField),
            Field('management_interface_id', AutoField),
            Field('credentials_readonly', NullBooleanField),
            Field('created_date', DateTimeUtcField),
            Field('credentials_descriptor', XMLField),
            Field('port', IntegerField),
            Field('description', CharField)
        ],
        attributes = dict(
            id=str
        ),
    )

@register
class EventType(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'event_type',
        elements = [
            Field('priority', SmallIntegerField),
            Field('event_type_id', AutoField),
            Field('name', CharField),
            Field('description', CharField)
        ],
        attributes = dict(
    
        ),
    )

@register
class ErrorResponse(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'error_response',
        elements = [
            Field('message', TextField),
            Field('code', TextField),
            Field('product_code', TextField),
            Field('traceback', TextField)
        ],
        attributes = dict(
    
        ),
    )

@register
class Pk(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'pk',
        elements = [
    
        ],
        attributes = dict(
    
        ),
    )

@register
class Inventory(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'inventory',
        elements = [
            Field('system_states', HrefField),
            Field('inventory_systems', HrefField),
            Field('system_types', HrefField),
            Field('infrastructure_systems', HrefField),
            Field('management_nodes', HrefField),
            Field('job_states', HrefField),
            Field('image_import_metadata_descriptor', HrefField),
            Field('zones', HrefField),
            Field('systems', HrefField),
            Field('management_interfaces', HrefField),
            Field('event_types', HrefField),
            Field('networks', HrefField),
            Field('log', HrefField)
        ],
        attributes = dict(
    
        ),
    )

@register
class Version(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'version',
        elements = [
            Field('full', TextField),
            Field('ordering', TextField),
            Field('version_id', AutoField),
            Field('label', TextField),
            Field('flavor', TextField),
            Field('revision', TextField)
        ],
        attributes = dict(
    
        ),
    )

@register
class SystemState(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'system_state',
        elements = [
            Field('system_state_id', AutoField),
            Field('created_date', DateTimeUtcField),
            Field('name', CharField),
            Field('description', CharField)
        ],
        attributes = dict(
            id=str
        ),
    )

@register
class Cache(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'cache',
        elements = [
    
        ],
        attributes = dict(
    
        ),
    )

@register
class ConfigurationDescriptor(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'configuration_descriptor',
        elements = [
    
        ],
        attributes = dict(
            id=str
        ),
    )

@register
class Zone(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'zone',
        elements = [
            Field('description', CharField),
            Field('created_date', DateTimeUtcField),
            Field('zone_id', AutoField),
            Field('name', CharField)
        ],
        attributes = dict(
            id=str
        ),
    )

@register
class SystemJobs(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'system_jobs',
        elements = [
            Field('SystemJobs', [Job])
        ],
        attributes = dict(
    
        ),
    )

@register
class SystemTypes(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'system_types',
        elements = [
            Field('SystemTypes', [SystemType])
        ],
        attributes = dict(
    
        ),
    )

@register
class SystemEvents(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'system_events',
        elements = [
            Field('SystemEvents', [system])
        ],
        attributes = dict(
    
        ),
    )

@register
class EventTypes(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'event_types',
        elements = [
            Field('EventTypes', [EventType])
        ],
        attributes = dict(
    
        ),
    )

@register
class Zones(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'zones',
        elements = [
            Field('Zones', [Zone])
        ],
        attributes = dict(
    
        ),
    )

@register
class Jobs(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'jobs',
        elements = [
            Field('Jobs', [Job])
        ],
        attributes = dict(
            id=str
        ),
    )

@register
class InstalledSoftware(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'installed_software',
        elements = [
            Field('InstalledSoftware', [version])
        ],
        attributes = dict(
            id=str
        ),
    )

@register
class SystemsLog(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'systems_log',
        elements = [
            Field('SystemsLog', [system_log])
        ],
        attributes = dict(
    
        ),
    )

@register
class ManagementInterfaces(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'management_interfaces',
        elements = [
            Field('ManagementInterfaces', [ManagementInterface])
        ],
        attributes = dict(
    
        ),
    )

@register
class SystemStates(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'system_states',
        elements = [
            Field('SystemStates', [SystemState])
        ],
        attributes = dict(
    
        ),
    )

@register
class ManagementNodes(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'management_nodes',
        elements = [
            Field('ManagementNodes', [zone])
        ],
        attributes = dict(
    
        ),
    )

@register
class Networks(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'networks',
        elements = [
            Field('systems', HrefField),
            Field('Networks', [system])
        ],
        attributes = dict(
    
        ),
    )

@register
class JobStates(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'job_states',
        elements = [
            Field('JobStates', [JobState])
        ],
        attributes = dict(
    
        ),
    )

@register
class Systems(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'systems',
        elements = [
            Field('Systems', [current_state])
        ],
        attributes = dict(
            count=int,
            next_page=str,
            num_pages=str,
            previous_page=str,
            full_collection=str,
            filter_by=str,
            limit=str,
            order_by=str,
            per_page=str,
            end_index=str,
            start_index=str
        ),
    )

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()

