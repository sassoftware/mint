# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models

class UrlField(object):
    def __init__(self, path):
    	self.path = path
    	
    def _getUrl(self, hostname, request):
    	return request.baseUrl;
    	
class RepositoryUrlField(UrlField):
    name = None
    def _getUrl(self, hostname, request):
        base = request.get_full_path()
        if base.endswith('/api'):
            base = base[:-4]
        return '%s/repos/%s/%s' % (request.gethost(), hostname, self.name)

class Users(models.Model):
    userid = models.IntegerField(primary_key=True)
    username = models.CharField(unique=True, max_length=128)
    fullname = models.CharField(max_length=128)
    salt = models.TextField() # This field type is a guess.
    passwd = models.CharField(max_length=254)
    email = models.CharField(max_length=128)
    displayemail = models.TextField()
    timecreated = models.DecimalField(max_digits=14, decimal_places=3)
    timeaccessed = models.DecimalField(max_digits=14, decimal_places=3)
    active = models.SmallIntegerField()
    blurb = models.TextField()
    class Meta:
        db_table = u'users'
        
    def __unicode__(self):
        return self.username

class Products(models.Model):
    productId = models.IntegerField(primary_key=True, db_column='projectid', blank=True)
    hostname = models.CharField(unique=True, max_length=63)
    name = models.CharField(unique=True, max_length=128)
    namespace = models.CharField(max_length=16)
    domainname = models.CharField(max_length=128)
    shortname = models.CharField(unique=True, max_length=63)
    projecturl = models.CharField(max_length=128, null=True, blank=True)
    repositoryHostName = models.CharField(max_length=255, db_column='fqdn')
    repositoryUrl      = RepositoryUrlField('api')
    repositoryBrowserUrl = RepositoryUrlField('browse')
    description = models.TextField(null=True, blank=True)
    prodtype = models.CharField(max_length=128)
    commitemail = models.CharField(max_length=128, null=True, blank=True)
    backupexternal = models.SmallIntegerField(null=True, blank=True)
    timecreated = models.DecimalField(max_digits=14, decimal_places=3, blank=True)
    timemodified = models.DecimalField(max_digits=14, decimal_places=3, blank=True)
    hidden = models.SmallIntegerField()
    creatorid = models.ForeignKey(Users, db_column='creatorid', related_name='creator', null=True)
    members = models.ManyToManyField(Users, through="Members", related_name='members')
    
    
    class Meta:
        db_table = u'projects'
        
    def __unicode__(self):
        return self.hostname
        
    def _attributes(self):
    	return ({'id': self.hostname})

class Members(models.Model):
    productId = models.ForeignKey(Products, db_column='projectid', related_name='product')
    userid = models.ForeignKey(Users, db_column='userid', related_name='user')
    level = models.SmallIntegerField()
    class Meta:
        db_table = u'projectusers'
        
class Versions(models.Model):
    productVersionId = models.IntegerField(primary_key=True)
    productId = models.ForeignKey(Products, db_column='projectid')
    namespace = models.CharField(max_length=16)
    name = models.CharField(max_length=16)
    description = models.TextField()
    timecreated = models.DecimalField(max_digits=14, decimal_places=3)
    class Meta:
        db_table = u'productversions'
        
    def __unicode__(self):
        return self.name
        

class Releases(models.Model):
    pubreleaseid = models.IntegerField(primary_key=True)
    productId = models.ForeignKey(Products, db_column='projectid', related_name='releasesProduct')
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=32)
    description = models.TextField()
    timecreated = models.DecimalField(max_digits=14, decimal_places=3)
    createdby = models.ForeignKey(Users, db_column='createdby', related_name='releaseCreator')
    timeupdated = models.DecimalField(max_digits=14, decimal_places=3)
    updatedby = models.ForeignKey(Users, db_column='updatedby', related_name='releaseUpdater')
    timepublished = models.DecimalField(max_digits=14, decimal_places=3)
    publishedby = models.ForeignKey(Users, db_column='publishedby', related_name='releasePublisher')
    shouldmirror = models.SmallIntegerField()
    timemirrored = models.DecimalField(max_digits=14, decimal_places=3)
    class Meta:
        db_table = u'publishedreleases'
     
    def __unicode__(self):
        return self.name
               
class Images(models.Model):
    imageId = models.IntegerField(primary_key=True, db_column='buildid')
    productId = models.ForeignKey(Products, db_column='projectid')
    pubreleaseid = models.ForeignKey(Releases, db_column='pubreleaseid')
    buildtype = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField()
    trovename = models.CharField(max_length=128)
    troveversion = models.CharField(max_length=255)
    troveflavor = models.CharField(max_length=4096)
    trovelastchanged = models.DecimalField(max_digits=14, decimal_places=3)
    timecreated = models.DecimalField(max_digits=14, decimal_places=3)
    createdby = models.ForeignKey(Users, db_column='createdby', related_name='imageCreator')
    timeupdated = models.DecimalField(max_digits=14, decimal_places=3)
    updatedby = models.ForeignKey(Users, db_column='updatedby', related_name='imageUpdater')
    deleted = models.SmallIntegerField()
    buildcount = models.IntegerField()
    productversionid = models.ForeignKey(Versions, db_column='productversionid')
    stagename = models.CharField(max_length=255)
    status = models.IntegerField()
    statusmessage = models.TextField()
    class Meta:
        db_table = u'builds'
        
    def __unicode__(self):
        return self.name
