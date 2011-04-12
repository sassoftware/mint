from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import SDKClassMeta, toUnderscore  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class Targets(object):
    """
    """
    __metaclass__ = SDKClassMeta
    targetid = 'IntegerField'
    targetname = 'CharField'
    targettype = 'CharField'

class Images(object):
    """
    """
    __metaclass__ = SDKClassMeta
    buildcount = 'IntegerField'
    buildtype = 'IntegerField'
    createdby = 'Users'
    deleted = 'SmallIntegerField'
    description = 'TextField'
    image_id = 'AutoField'
    name = 'CharField'
    product_id = 'Products'
    productversionid = 'Versions'
    pubreleaseid = 'Releases'
    stagename = 'CharField'
    status = 'IntegerField'
    statusmessage = 'TextField'
    timecreated = 'DecimalField'
    timeupdated = 'DecimalField'
    troveflavor = 'CharField'
    trovelastchanged = 'DecimalField'
    trovename = 'CharField'
    troveversion = 'CharField'
    updatedby = 'Users'

class UserGroups(object):
    """
    """
    __metaclass__ = SDKClassMeta
    usergroup = 'CharField'
    usergroupid = 'AutoField'

class TargetUserCredentials(object):
    """
    """
    __metaclass__ = SDKClassMeta
    id = 'AutoField'
    targetcredentialsid = 'TargetCredentials'
    targetid = 'Targets'
    userid = 'Users'

class Products(object):
    """
    """
    __metaclass__ = SDKClassMeta
    backupexternal = 'SmallIntegerField'
    commitemail = 'CharField'
    creatorid = 'Users'
    description = 'TextField'
    domainname = 'CharField'
    hidden = 'SmallIntegerField'
    hostname = 'CharField'
    name = 'CharField'
    namespace = 'CharField'
    prodtype = 'CharField'
    product_id = 'AutoField'
    projecturl = 'CharField'
    repository_host_name = 'CharField'
    shortname = 'CharField'
    timecreated = 'DecimalField'
    timemodified = 'DecimalField'

class PkiCertificates(object):
    """
    """
    __metaclass__ = SDKClassMeta
    ca_serial_index = 'IntegerField'
    fingerprint = 'TextField'
    is_ca = 'BooleanField'
    issuer_fingerprint = 'PkiCertificates'
    pkey_pem = 'TextField'
    purpose = 'TextField'
    time_expired = 'DateTimeUtcField'
    time_issued = 'DateTimeUtcField'
    x509_pem = 'TextField'

class Fault(object):
    """
    """
    __metaclass__ = SDKClassMeta
    code = 'IntegerField'
    message = 'CharField'
    traceback = 'TextField'

class UserGroupMembers(object):
    """
    """
    __metaclass__ = SDKClassMeta
    id = 'AutoField'
    usergroupid = 'UserGroups'
    userid = 'Users'

class TargetImagesDeployed(object):
    """
    """
    __metaclass__ = SDKClassMeta
    fileid = 'IntegerField'
    id = 'AutoField'
    targetid = 'Targets'
    targetimageid = 'CharField'

class DatabaseVersion(object):
    """
    """
    __metaclass__ = SDKClassMeta
    id = 'AutoField'
    minor = 'SmallIntegerField'
    version = 'SmallIntegerField'

class Members(object):
    """
    """
    __metaclass__ = SDKClassMeta
    id = 'AutoField'
    level = 'SmallIntegerField'
    product_id = 'Products'
    userid = 'Users'

class Versions(object):
    """
    """
    __metaclass__ = SDKClassMeta
    description = 'TextField'
    name = 'CharField'
    namespace = 'CharField'
    product_id = 'Products'
    product_version_id = 'AutoField'
    timecreated = 'DecimalField'

class Downloads(object):
    """
    """
    __metaclass__ = SDKClassMeta
    id = 'AutoField'
    image_id = 'Images'
    ip = 'CharField'
    timedownloaded = 'CharField'

class Sessions(object):
    """
    """
    __metaclass__ = SDKClassMeta
    data = 'TextField'
    session_id = 'AutoField'
    sid = 'CharField'

class Releases(object):
    """
    """
    __metaclass__ = SDKClassMeta
    createdby = 'Users'
    description = 'TextField'
    name = 'CharField'
    product_id = 'Products'
    publishedby = 'Users'
    pubreleaseid = 'AutoField'
    shouldmirror = 'SmallIntegerField'
    timecreated = 'DecimalField'
    timemirrored = 'DecimalField'
    timepublished = 'DecimalField'
    timeupdated = 'DecimalField'
    updatedby = 'Users'
    version = 'CharField'

class Users(object):
    """
    """
    __metaclass__ = SDKClassMeta
    active = 'SmallIntegerField'
    blurb = 'TextField'
    displayemail = 'TextField'
    email = 'CharField'
    fullname = 'CharField'
    passwd = 'CharField'
    salt = 'TextField'
    timeaccessed = 'DecimalField'
    timecreated = 'DecimalField'
    userid = 'AutoField'
    username = 'CharField'

class Jobs(object):
    """
    """
    __metaclass__ = SDKClassMeta
    job_id = 'AutoField'
    job_uuid = 'TextField'

class TargetCredentials(object):
    """
    """
    __metaclass__ = SDKClassMeta
    credentials = 'TextField'
    targetcredentialsid = 'AutoField'

class Pk(object):
    """
    """
    __metaclass__ = SDKClassMeta

class TargetData(object):
    """
    """
    __metaclass__ = SDKClassMeta
    id = 'AutoField'
    name = 'CharField'
    targetid = 'Targets'
    value = 'TextField'

# DO NOT TOUCH #
GLOBALS = globals()
for tag, clsAttrs in REGISTRY.items():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]
    for attrName, refClsOrName in clsAttrs.items():
        if refClsOrName in GLOBALS:
            cls, refCls = GLOBALS[tag], GLOBALS[refClsOrName]
            if isinstance(getattr(cls, attrName), list):
                setattr(cls, attrName, [refCls])
            else:
                setattr(cls, attrName, refCls)

