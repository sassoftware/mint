from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import RegistryMeta  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class Targets(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    targettype = CharField
    targetname = CharField
    targetid = IntegerField

class Images(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    updatedby = Users
    troveversion = CharField
    trovename = CharField
    trovelastchanged = DecimalField
    troveflavor = CharField
    timeupdated = DecimalField
    timecreated = DecimalField
    statusmessage = TextField
    status = IntegerField
    stagename = CharField
    pubreleaseid = Releases
    productversionid = Versions
    product_id = Products
    name = CharField
    image_id = AutoField
    description = TextField
    deleted = SmallIntegerField
    createdby = Users
    buildtype = IntegerField
    buildcount = IntegerField

class UserGroups(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    usergroupid = AutoField
    usergroup = CharField

class TargetUserCredentials(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    userid = Users
    targetid = Targets
    targetcredentialsid = TargetCredentials
    id = AutoField

class Products(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    timemodified = DecimalField
    timecreated = DecimalField
    shortname = CharField
    repository_host_name = CharField
    projecturl = CharField
    product_id = AutoField
    prodtype = CharField
    namespace = CharField
    name = CharField
    hostname = CharField
    hidden = SmallIntegerField
    domainname = CharField
    description = TextField
    creatorid = Users
    commitemail = CharField
    backupexternal = SmallIntegerField

class PkiCertificates(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    x509_pem = TextField
    time_issued = DateTimeUtcField
    time_expired = DateTimeUtcField
    purpose = TextField
    pkey_pem = TextField
    issuer_fingerprint = PkiCertificates
    is_ca = BooleanField
    fingerprint = TextField
    ca_serial_index = IntegerField

class Fault(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    traceback = TextField
    message = CharField
    code = IntegerField

class UserGroupMembers(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    userid = Users
    usergroupid = UserGroups
    id = AutoField

class TargetImagesDeployed(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    targetimageid = CharField
    targetid = Targets
    id = AutoField
    fileid = IntegerField

class DatabaseVersion(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    version = SmallIntegerField
    minor = SmallIntegerField
    id = AutoField

class Members(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    userid = Users
    product_id = Products
    level = SmallIntegerField
    id = AutoField

class Versions(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    timecreated = DecimalField
    product_version_id = AutoField
    product_id = Products
    namespace = CharField
    name = CharField
    description = TextField

class Downloads(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    timedownloaded = CharField
    ip = CharField
    image_id = Images
    id = AutoField

class Sessions(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    sid = CharField
    session_id = AutoField
    data = TextField

class Releases(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    version = CharField
    updatedby = Users
    timeupdated = DecimalField
    timepublished = DecimalField
    timemirrored = DecimalField
    timecreated = DecimalField
    shouldmirror = SmallIntegerField
    pubreleaseid = AutoField
    publishedby = Users
    product_id = Products
    name = CharField
    description = TextField
    createdby = Users

class Users(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    username = CharField
    userid = AutoField
    timecreated = DecimalField
    timeaccessed = DecimalField
    salt = TextField
    passwd = CharField
    fullname = CharField
    email = CharField
    displayemail = TextField
    blurb = TextField
    active = SmallIntegerField

class Jobs(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    job_uuid = TextField
    job_id = AutoField

class TargetCredentials(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    targetcredentialsid = AutoField
    credentials = TextField

class Pk(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    

class TargetData(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    value = TextField
    targetid = Targets
    name = CharField
    id = AutoField

# DO NOT TOUCH #
GLOBALS = globals()
for tag, clsAttrs in REGISTRY.items():
    if tag in GLOBALS:
        TYPEMAP[tag.lower()] = GLOBALS[tag]
    for attrName, refClsOrName in clsAttrs.items():
        if refClsOrName in GLOBALS:
            cls = GLOBALS[tag]
            refCls = GLOBALS[refClsOrName]
            if isinstance(getattr(cls, attrName), list):
                setattr(cls, attrName, [refCls])
            else:
                setattr(cls, attrName, refCls)

