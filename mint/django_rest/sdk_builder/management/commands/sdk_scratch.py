#  pyflakes=ignore
#
# Copyright (c) 2011 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

# for debugging purposes, only use mint.django_rest.rbuilder.inventory.models
# at first
from mint.django_rest.rbuilder.inventory import models

from django.core.management.base import BaseCommand
from mint.django_rest.sdk_builder import sdk
from mint.django_rest.sdk_builder import sdkutils
import inspect
from xobj import xobj
import os

###### Sample Crap For Testing Purposes ######
    
PKGS_XML = \
"""
<packages>
    <data pid="1">my data</data>
    <package pid="http://localhost/api/packages/1">
        <name>Apache</name>
        <description>Server</description>
    </package>
    <package pid="http://localhost/api/packages/2">
        <name>Nano</name>
        <description>Text Editor</description>
    </package>
</packages>
""".strip()

CXML = \
"""
<catalog cid="1">
    <url tags="hello world, greeting, common">
        http://helloworld.com/
    </url>
    <url tags="goodbye world, farewell, common">
        http://goodbyeworld.com/
    </url>
</catalog>
""".strip()


class Url(xobj.XObj, XObjMixin):
    __metaclass__ = sdk.GetSetXMLAttrMeta

    tags = sdk.Fields.TextField

class Catalog(xobj.XObj, XObjMixin):
    __metaclass__ = sdk.GetSetXMLAttrMeta

    cid = sdk.Fields.IntegerField
    url = [Url]


class Data(xobj.XObj, XObjMixin):
    __metaclass__ = sdk.GetSetXMLAttrMeta
    
    pid = sdk.Fields.IntegerField
    

class Package(xobj.XObj, XObjMixin):
    __metaclass__ = sdk.GetSetXMLAttrMeta
    
    pid = sdk.Fields.URLField
    name = sdk.Fields.CharField
    description = sdk.Fields.TextField

class Packages(xobj.XObj, XObjMixin):
    __metaclass__ = sdk.GetSetXMLAttrMeta
    
    package = [Package]
    data = Data
    
##############################################

class Command(BaseCommand):
    help = "Generates python sdk"

    def handle(self, *args, **options):
        """
        Generates Python SDK for REST API
        """
        
        ##### For testing purposes only #####
        doc = xobj.parse(PKGS_XML, typeMap={'packages':Packages, 'data':Data})  # pyflakes=ignore
        
        # assignment works but shouldn't work (should throw assertion error)
        # doc.packages.package[0].name = u'new name' # FIXED
        
        import pdb; pdb.set_trace()
        print doc.packages.data['pid']
        
        import pdb; pdb.set_trace()
        
        # assignment fails but *should* fail (throws assertion error)
        # doc.packages.data.pid = 1
        
        # assignment works and *should* work
        # doc.packages.data.pid = sdk.Fields.IntegerField(1)
        
        # assignment works but shouldn't work (should throw assertion error)
        # doc.packages.package[0].pid = 2 # FIXED
        
        # notice that doc.toxml() leaves doc.packages.data empty
        # this is still most likely because Data is being registered
        # as a complexType.  Also is weird because if I leave the Data
        # class stub as empty, the data+id are correctly displayed.
        # This doesn't make sense because I don't have this problem
        # with Package.
        print doc.toxml()
        # notice that this should also fail, I should *not* be able to
        # assign an integer where instance of Data is needed.
        # doc.packages.data = 3 # FIXED
        
        import pdb; pdb.set_trace()
        # however, the following works (and should work)
        doc.packages.data = Data('Hello World')
        # doc.toxml() correctly includes and renders doc.packages.data
        # however it is missing the id:
        import pdb; pdb.set_trace()
        print doc.toxml()
        # we can assign an id -- below does *not* work and shouldn't work
        # doc.packages.data.pid = 'X'
        # we can assign an id -- below *does* work and should work
        # doc.packages.data.pid = sdk.Fields.IntegerField(1)
        p = Package()
        p.description = sdk.Fields.TextField('a new package')
        p.pid = sdk.Fields.URLField('http://helloworld.com/')
        p.name = sdk.Fields.CharField('my new pkg')
        # doc.toxml() now renders what we expect to see
        doc.packages.package.append(p)
        
        print doc.toxml()
        
        print '\n'
        print '\n'
        
        doc2 = xobj.parse(CXML, typeMap={'catalog':Catalog, 'url':Url})
        
        import pdb; pdb.set_trace()
        pass
        ############## END ##################
