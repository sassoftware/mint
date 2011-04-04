from sdk import Fields
from sdk import XObjMixin
from sdk import GetSetXMLAttrMeta
from xobj import xobj


class rbuilder(object):
    """rbuilder"""

    class TargetData(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        name = Fields.CharField
        targetid = Fields.ForeignKey
        value = Fields.TextField
        id = Fields.AutoField
    
    class Pk(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class TargetCredentials(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        credentials = Fields.TextField
        targetcredentialsid = Fields.AutoField
    
    class Jobs(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        job_id = Fields.AutoField
        job_uuid = Fields.TextField
    
    class Users(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        username = Fields.CharField
        timecreated = Fields.DecimalField
        passwd = Fields.CharField
        userid = Fields.AutoField
        displayemail = Fields.TextField
        blurb = Fields.TextField
        active = Fields.SmallIntegerField
        fullname = Fields.CharField
        salt = Fields.TextField
        email = Fields.CharField
        timeaccessed = Fields.DecimalField
    
    class Releases(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        timemirrored = Fields.DecimalField
        description = Fields.TextField
        timecreated = Fields.DecimalField
        pubreleaseid = Fields.AutoField
        timepublished = Fields.DecimalField
        updatedby = Fields.ForeignKey
        name = Fields.CharField
        version = Fields.CharField
        shouldmirror = Fields.SmallIntegerField
        createdby = Fields.ForeignKey
        timeupdated = Fields.DecimalField
        publishedby = Fields.ForeignKey
        productid = Fields.ForeignKey
    
    class Sessions(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        sessionid = Fields.AutoField
        data = Fields.TextField
        sid = Fields.CharField
    
    class Downloads(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        ip = Fields.CharField
        timedownloaded = Fields.CharField
        id = Fields.AutoField
        imageid = Fields.ForeignKey
    
    class Versions(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        name = Fields.CharField
        timecreated = Fields.DecimalField
        productversionid = Fields.AutoField
        description = Fields.TextField
        namespace = Fields.CharField
        productid = Fields.ForeignKey
    
    class Members(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        level = Fields.SmallIntegerField
        userid = Fields.ForeignKey
        id = Fields.AutoField
        productid = Fields.ForeignKey
    
    class DatabaseVersion(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        version = Fields.SmallIntegerField
        id = Fields.AutoField
        minor = Fields.SmallIntegerField
    
    class TargetImagesDeployed(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        targetid = Fields.ForeignKey
        id = Fields.AutoField
        targetimageid = Fields.CharField
        fileid = Fields.IntegerField
    
    class UserGroupMembers(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        userid = Fields.ForeignKey
        id = Fields.AutoField
        usergroupid = Fields.ForeignKey
    
    class Fault(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        message = Fields.CharField
        code = Fields.IntegerField
        traceback = Fields.TextField
    
    class PkiCertificates(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        is_ca = Fields.BooleanField
        pkey_pem = Fields.TextField
        fingerprint = Fields.TextField
        time_expired = Fields.DateTimeUtcField
        ca_serial_index = Fields.IntegerField
        purpose = Fields.TextField
        x509_pem = Fields.TextField
        issuer_fingerprint = Fields.ForeignKey
        time_issued = Fields.DateTimeUtcField
    
    class Products(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        backupexternal = Fields.SmallIntegerField
        repositoryhostname = Fields.CharField
        domainname = Fields.CharField
        creatorid = Fields.ForeignKey
        hidden = Fields.SmallIntegerField
        description = Fields.TextField
        projecturl = Fields.CharField
        name = Fields.CharField
        timecreated = Fields.DecimalField
        hostname = Fields.CharField
        namespace = Fields.CharField
        commitemail = Fields.CharField
        prodtype = Fields.CharField
        shortname = Fields.CharField
        timemodified = Fields.DecimalField
        productid = Fields.AutoField
    
    class TargetUserCredentials(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        targetid = Fields.ForeignKey
        userid = Fields.ForeignKey
        targetcredentialsid = Fields.ForeignKey
        id = Fields.AutoField
    
    class UserGroups(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        usergroupid = Fields.AutoField
        usergroup = Fields.CharField
    
    class Images(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        status = Fields.IntegerField
        buildtype = Fields.IntegerField
        description = Fields.TextField
        pubreleaseid = Fields.ForeignKey
        deleted = Fields.SmallIntegerField
        trovelastchanged = Fields.DecimalField
        imageid = Fields.AutoField
        timeupdated = Fields.DecimalField
        productversionid = Fields.ForeignKey
        statusmessage = Fields.TextField
        name = Fields.CharField
        stagename = Fields.CharField
        timecreated = Fields.DecimalField
        troveversion = Fields.CharField
        troveflavor = Fields.CharField
        trovename = Fields.CharField
        createdby = Fields.ForeignKey
        updatedby = Fields.ForeignKey
        buildcount = Fields.IntegerField
        productid = Fields.ForeignKey
    
    class Targets(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        targettype = Fields.CharField
        targetname = Fields.CharField
        targetid = Fields.IntegerField

