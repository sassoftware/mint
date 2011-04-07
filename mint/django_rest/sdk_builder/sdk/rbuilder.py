from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import XObjMixin
from sdk.rSDK import GetSetXMLAttrMeta
from xobj.xobj import XObj


class Targets(XObj, XObjMixin):
    """
    """
    targettype = CharField
    targetname = CharField
    targetid = IntegerField

class Images(XObj, XObjMixin):
    """
    """
    updatedby = ForeignKey
    troveversion = CharField
    trovename = CharField
    trovelastchanged = DecimalField
    troveflavor = CharField
    timeupdated = DecimalField
    timecreated = DecimalField
    statusmessage = TextField
    status = IntegerField
    stagename = CharField
    pubreleaseid = ForeignKey
    productversionid = ForeignKey
    product_id = ForeignKey
    name = CharField
    image_id = AutoField
    description = TextField
    deleted = SmallIntegerField
    createdby = ForeignKey
    buildtype = IntegerField
    buildcount = IntegerField

class UserGroups(XObj, XObjMixin):
    """
    """
    usergroupid = AutoField
    usergroup = CharField

class TargetUserCredentials(XObj, XObjMixin):
    """
    """
    userid = ForeignKey
    targetid = ForeignKey
    targetcredentialsid = ForeignKey
    id = AutoField

class Products(XObj, XObjMixin):
    """
    """
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
    creatorid = ForeignKey
    commitemail = CharField
    backupexternal = SmallIntegerField

class PkiCertificates(XObj, XObjMixin):
    """
    """
    x509_pem = TextField
    time_issued = DateTimeUtcField
    time_expired = DateTimeUtcField
    purpose = TextField
    pkey_pem = TextField
    issuer_fingerprint = ForeignKey
    is_ca = BooleanField
    fingerprint = TextField
    ca_serial_index = IntegerField

class Fault(XObj, XObjMixin):
    """
    """
    traceback = TextField
    message = CharField
    code = IntegerField

class UserGroupMembers(XObj, XObjMixin):
    """
    """
    userid = ForeignKey
    usergroupid = ForeignKey
    id = AutoField

class TargetImagesDeployed(XObj, XObjMixin):
    """
    """
    targetimageid = CharField
    targetid = ForeignKey
    id = AutoField
    fileid = IntegerField

class DatabaseVersion(XObj, XObjMixin):
    """
    """
    version = SmallIntegerField
    minor = SmallIntegerField
    id = AutoField

class Members(XObj, XObjMixin):
    """
    """
    userid = ForeignKey
    product_id = ForeignKey
    level = SmallIntegerField
    id = AutoField

class Versions(XObj, XObjMixin):
    """
    """
    timecreated = DecimalField
    product_version_id = AutoField
    product_id = ForeignKey
    namespace = CharField
    name = CharField
    description = TextField

class Downloads(XObj, XObjMixin):
    """
    """
    timedownloaded = CharField
    ip = CharField
    image_id = ForeignKey
    id = AutoField

class Sessions(XObj, XObjMixin):
    """
    """
    sid = CharField
    session_id = AutoField
    data = TextField

class Releases(XObj, XObjMixin):
    """
    """
    version = CharField
    updatedby = ForeignKey
    timeupdated = DecimalField
    timepublished = DecimalField
    timemirrored = DecimalField
    timecreated = DecimalField
    shouldmirror = SmallIntegerField
    pubreleaseid = AutoField
    publishedby = ForeignKey
    product_id = ForeignKey
    name = CharField
    description = TextField
    createdby = ForeignKey

class Users(XObj, XObjMixin):
    """
    """
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

class Jobs(XObj, XObjMixin):
    """
    """
    job_uuid = TextField
    job_id = AutoField

class TargetCredentials(XObj, XObjMixin):
    """
    """
    targetcredentialsid = AutoField
    credentials = TextField

class Pk(XObj, XObjMixin):
    """
    """

class TargetData(XObj, XObjMixin):
    """
    """
    value = TextField
    targetid = ForeignKey
    name = CharField
    id = AutoField

