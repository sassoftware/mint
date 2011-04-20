from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import SDKClassMeta, toUnderscore, register, DynamicImportResolver  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

@register
class Targets(object):
    """
    """
    __metaclass__ = SDKClassMeta
    targettype = 'CharField'
    targetname = 'CharField'
    targetid = 'IntegerField'

@register
class Images(object):
    """
    """
    __metaclass__ = SDKClassMeta
    updatedby = 'Users'
    troveversion = 'CharField'
    trovename = 'CharField'
    trovelastchanged = 'DecimalField'
    troveflavor = 'CharField'
    timeupdated = 'DecimalField'
    timecreated = 'DecimalField'
    statusmessage = 'TextField'
    status = 'IntegerField'
    stagename = 'CharField'
    pubreleaseid = 'Releases'
    productversionid = 'Versions'
    product_id = 'Products'
    name = 'CharField'
    image_id = 'AutoField'
    description = 'TextField'
    deleted = 'SmallIntegerField'
    createdby = 'Users'
    buildtype = 'IntegerField'
    buildcount = 'IntegerField'

@register
class UserGroups(object):
    """
    """
    __metaclass__ = SDKClassMeta
    usergroupid = 'AutoField'
    usergroup = 'CharField'

@register
class TargetUserCredentials(object):
    """
    """
    __metaclass__ = SDKClassMeta
    userid = 'Users'
    targetid = 'Targets'
    targetcredentialsid = 'TargetCredentials'
    id = 'AutoField'

@register
class Products(object):
    """
    """
    __metaclass__ = SDKClassMeta
    timemodified = 'DecimalField'
    timecreated = 'DecimalField'
    shortname = 'CharField'
    repository_host_name = 'CharField'
    projecturl = 'CharField'
    product_id = 'AutoField'
    prodtype = 'CharField'
    namespace = 'CharField'
    name = 'CharField'
    hostname = 'CharField'
    hidden = 'SmallIntegerField'
    domainname = 'CharField'
    description = 'TextField'
    creatorid = 'Users'
    commitemail = 'CharField'
    backupexternal = 'SmallIntegerField'

@register
class PkiCertificates(object):
    """
    """
    __metaclass__ = SDKClassMeta
    x509_pem = 'TextField'
    time_issued = 'DateTimeUtcField'
    time_expired = 'DateTimeUtcField'
    purpose = 'TextField'
    pkey_pem = 'TextField'
    issuer_fingerprint = 'PkiCertificates'
    is_ca = 'BooleanField'
    fingerprint = 'TextField'
    ca_serial_index = 'IntegerField'

@register
class Fault(object):
    """
    """
    __metaclass__ = SDKClassMeta
    traceback = 'TextField'
    message = 'CharField'
    code = 'IntegerField'

@register
class UserGroupMembers(object):
    """
    """
    __metaclass__ = SDKClassMeta
    userid = 'Users'
    usergroupid = 'UserGroups'
    id = 'AutoField'

@register
class TargetImagesDeployed(object):
    """
    """
    __metaclass__ = SDKClassMeta
    targetimageid = 'CharField'
    targetid = 'Targets'
    id = 'AutoField'
    fileid = 'IntegerField'

@register
class DatabaseVersion(object):
    """
    """
    __metaclass__ = SDKClassMeta
    version = 'SmallIntegerField'
    minor = 'SmallIntegerField'
    id = 'AutoField'

@register
class Members(object):
    """
    """
    __metaclass__ = SDKClassMeta
    userid = 'Users'
    product_id = 'Products'
    level = 'SmallIntegerField'
    id = 'AutoField'

@register
class Versions(object):
    """
    """
    __metaclass__ = SDKClassMeta
    timecreated = 'DecimalField'
    product_version_id = 'AutoField'
    product_id = 'Products'
    namespace = 'CharField'
    name = 'CharField'
    description = 'TextField'

@register
class Downloads(object):
    """
    """
    __metaclass__ = SDKClassMeta
    timedownloaded = 'CharField'
    ip = 'CharField'
    image_id = 'Images'
    id = 'AutoField'

@register
class Sessions(object):
    """
    """
    __metaclass__ = SDKClassMeta
    sid = 'CharField'
    session_id = 'AutoField'
    data = 'TextField'

@register
class Releases(object):
    """
    """
    __metaclass__ = SDKClassMeta
    version = 'CharField'
    updatedby = 'Users'
    timeupdated = 'DecimalField'
    timepublished = 'DecimalField'
    timemirrored = 'DecimalField'
    timecreated = 'DecimalField'
    shouldmirror = 'SmallIntegerField'
    pubreleaseid = 'AutoField'
    publishedby = 'Users'
    product_id = 'Products'
    name = 'CharField'
    description = 'TextField'
    createdby = 'Users'

@register
class Users(object):
    """
    """
    __metaclass__ = SDKClassMeta
    username = 'CharField'
    userid = 'AutoField'
    timecreated = 'DecimalField'
    timeaccessed = 'DecimalField'
    salt = 'TextField'
    passwd = 'CharField'
    fullname = 'CharField'
    email = 'CharField'
    displayemail = 'TextField'
    blurb = 'TextField'
    active = 'SmallIntegerField'

@register
class Jobs(object):
    """
    """
    __metaclass__ = SDKClassMeta
    job_uuid = 'TextField'
    job_id = 'AutoField'

@register
class TargetCredentials(object):
    """
    """
    __metaclass__ = SDKClassMeta
    targetcredentialsid = 'AutoField'
    credentials = 'TextField'

@register
class Pk(object):
    """
    """
    __metaclass__ = SDKClassMeta

@register
class TargetData(object):
    """
    """
    __metaclass__ = SDKClassMeta
    value = 'TextField'
    targetid = 'Targets'
    name = 'CharField'
    id = 'AutoField'

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()
for tag in REGISTRY.keys():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]

