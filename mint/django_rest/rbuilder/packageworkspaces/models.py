#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#
import sys
from django.db import models
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from xobj import xobj

from mint.django_rest.rbuilder import models as rbuildermodels

class PackageWorkspaces(modellib.XObjModel):
    XSL = 'packageWorkspaces.xsl'
    
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='package_workspaces',
                elements=['package_workspace'])
    list_fields = ['package_workspace']
    
    
class PackageWorkspace(modellib.XObjIdModel):
    XSL = "packageWorkspace.xsl"
    
    class Meta:
        db_table = 'package_workspace_workspace'
    _xobj = xobj.XObjMetadata(
                tag = 'package_workspace')
    
    package_workspace_id = D(models.AutoField(primary_key=True), "Database id of package workspace")
    package_workspace_name = D(models.CharField(max_length=100), "Name of workspace")
    package_workspace_version = D(models.CharField(max_length=100), "Version")
    # package_workspace_files = D(models.ForeignKey(PackageWorkspaceFile, 
    #                             db_column="pwfilesid", refName='id'), "Collection of files")

    
class PackageWorkspaceFiles(modellib.XObjModel):
    XSL = "packageWorkspaceFiles.xsl"

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'package_workspace_files',
                elements=['package_workspace_file'])
    list_fields = ['packageworkspacefile']
    
    
class PackageWorkspaceFile(modellib.XObjIdModel):
    XSL = "packageWorkspaceFile.xsl"

    class Meta:
        db_table = 'package_workspace_file'
    _xobj = xobj.XObjMetadata(
                tag = 'package_workspace_file',
                attributes = {'id':str})   
    
    file_url = D(models.URLField(), "URL of file")
    file_size = D(models.IntegerField(), "Size of file")
    
    
    
for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
for mod_obj in rbuildermodels.__dict__.values():
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj    