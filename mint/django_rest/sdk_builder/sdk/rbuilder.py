from rSDK.Fields import *  # pyflakes=ignore
from rSDK import XObjMixin
from rSDK import GetSetXMLAttrMeta
from xobj import xobj


class Targets(XObj, XObjMixin):
    """
    """
    targettype = CharField
    targetname = CharField
    targetid = IntegerField

class Images(XObj, XObjMixin):
    """
    """
    status = IntegerField
    buildtype = IntegerField
    description = TextField
    pubreleaseid = ForeignKey
    deleted = SmallIntegerField
    trovelastchanged = DecimalField
    imageId = AutoField
    timeupdated = DecimalField
    productversionid = ForeignKey
    statusmessage = TextField
    name = CharField
    stagename = CharField
    timecreated = DecimalField
    troveversion = CharField
    troveflavor = CharField
    trovename = CharField
    createdby = ForeignKey
    updatedby = ForeignKey
    buildcount = IntegerField
    productId = ForeignKey

class UserGroups(XObj, XObjMixin):
    """
    """
    usergroupid = AutoField
    usergroup = CharField

class TargetUserCredentials(XObj, XObjMixin):
    """
    """
    targetid = ForeignKey
    userid = ForeignKey
    targetcredentialsid = ForeignKey
    id = AutoField

class Products(XObj, XObjMixin):
    """
    """
    backupexternal = SmallIntegerField
    repositoryHostName = CharField
    domainname = CharField
    creatorid = ForeignKey
    hidden = SmallIntegerField
    description = TextField
    projecturl = CharField
    name = CharField
    timecreated = DecimalField
    hostname = CharField
    namespace = CharField
    commitemail = CharField
    prodtype = CharField
    shortname = CharField
    timemodified = DecimalField
    productId = AutoField

class PkiCertificates(XObj, XObjMixin):
    """
    """
    is_ca = BooleanField
    pkey_pem = TextField
    fingerprint = TextField
    time_expired = DateTimeUtcField
    ca_serial_index = IntegerField
    purpose = TextField
    x509_pem = TextField
    issuer_fingerprint = ForeignKey
    time_issued = DateTimeUtcField

class Fault(XObj, XObjMixin):
    """
    """
    message = CharField
    code = IntegerField
    traceback = TextField

class UserGroupMembers(XObj, XObjMixin):
    """
    """
    userid = ForeignKey
    id = AutoField
    usergroupid = ForeignKey

class TargetImagesDeployed(XObj, XObjMixin):
    """
    """
    targetid = ForeignKey
    id = AutoField
    targetimageid = CharField
    fileid = IntegerField

class DatabaseVersion(XObj, XObjMixin):
    """
    """
    version = SmallIntegerField
    id = AutoField
    minor = SmallIntegerField

class Members(XObj, XObjMixin):
    """
    """
    level = SmallIntegerField
    userid = ForeignKey
    id = AutoField
    productId = ForeignKey

class Versions(XObj, XObjMixin):
    """
    """
    name = CharField
    timecreated = DecimalField
    productVersionId = AutoField
    description = TextField
    namespace = CharField
    productId = ForeignKey

class Downloads(XObj, XObjMixin):
    """
    """
    ip = CharField
    timedownloaded = CharField
    id = AutoField
    imageId = ForeignKey

class Sessions(XObj, XObjMixin):
    """
    """
    sessionId = AutoField
    data = TextField
    sid = CharField

class Releases(XObj, XObjMixin):
    """
    """
    timemirrored = DecimalField
    description = TextField
    timecreated = DecimalField
    pubreleaseid = AutoField
    timepublished = DecimalField
    updatedby = ForeignKey
    name = CharField
    version = CharField
    shouldmirror = SmallIntegerField
    createdby = ForeignKey
    timeupdated = DecimalField
    publishedby = ForeignKey
    productId = ForeignKey

class Users(XObj, XObjMixin):
    """
    """
    username = CharField
    timecreated = DecimalField
    passwd = CharField
    userid = AutoField
    displayemail = TextField
    blurb = TextField
    active = SmallIntegerField
    fullname = CharField
    salt = TextField
    email = CharField
    timeaccessed = DecimalField

class Jobs(XObj, XObjMixin):
    """
    """
    job_id = AutoField
    job_uuid = TextField

class TargetCredentials(XObj, XObjMixin):
    """
    """
    credentials = TextField
    targetcredentialsid = AutoField

class Pk(XObj, XObjMixin):
    """
    """

class TargetData(XObj, XObjMixin):
    """
    """
    name = CharField
    targetid = ForeignKey
    value = TextField
    id = AutoField

