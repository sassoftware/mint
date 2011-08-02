from rsdk.Fields import *  # pyflakes=ignore
from rsdk.sdk import SDKModel, toUnderscore, register, DynamicImportResolver  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

@register
class Targets(SDKModel):
    """ """

    targettype = 'CharField'
    targetname = 'CharField'
    targetid = 'IntegerField'

@register
class Images(SDKModel):
    """ """

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
class UserGroups(SDKModel):
    """ """

    usergroupid = 'AutoField'
    usergroup = 'CharField'

@register
class TargetUserCredentials(SDKModel):
    """ """

    userid = 'Users'
    targetid = 'Targets'
    targetcredentialsid = 'TargetCredentials'
    id = 'AutoField'

@register
class Products(SDKModel):
    """ """

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
class PkiCertificates(SDKModel):
    """ """

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
class Fault(SDKModel):
    """ """

    traceback = 'TextField'
    message = 'CharField'
    code = 'IntegerField'

@register
class UserGroupMembers(SDKModel):
    """ """

    userid = 'Users'
    usergroupid = 'UserGroups'
    id = 'AutoField'

@register
class TargetImagesDeployed(SDKModel):
    """ """

    targetimageid = 'CharField'
    targetid = 'Targets'
    id = 'AutoField'
    fileid = 'IntegerField'

@register
class DatabaseVersion(SDKModel):
    """ """

    version = 'SmallIntegerField'
    minor = 'SmallIntegerField'
    id = 'AutoField'

@register
class Members(SDKModel):
    """ """

    userid = 'Users'
    product_id = 'Products'
    level = 'SmallIntegerField'
    id = 'AutoField'

@register
class Versions(SDKModel):
    """ """

    timecreated = 'DecimalField'
    product_version_id = 'AutoField'
    product_id = 'Products'
    namespace = 'CharField'
    name = 'CharField'
    description = 'TextField'

@register
class Downloads(SDKModel):
    """ """

    timedownloaded = 'CharField'
    ip = 'CharField'
    image_id = 'Images'
    id = 'AutoField'

@register
class Sessions(SDKModel):
    """ """

    sid = 'CharField'
    session_id = 'AutoField'
    data = 'TextField'

@register
class Releases(SDKModel):
    """ """

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
class Users(SDKModel):
    """ """

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
class Jobs(SDKModel):
    """ """

    job_uuid = 'TextField'
    job_id = 'AutoField'

@register
class TargetCredentials(SDKModel):
    """ """

    targetcredentialsid = 'AutoField'
    credentials = 'TextField'

@register
class Pk(SDKModel):
    """ """


@register
class TargetData(SDKModel):
    """ """

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

