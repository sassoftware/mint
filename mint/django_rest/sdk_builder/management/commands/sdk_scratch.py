# #
# # Copyright (c) 2011 rPath, Inc.
# #
# # This program is distributed under the terms of the Common Public License,
# # version 1.0. A copy of this license should have been distributed with this
# # source file in a file called LICENSE. If it is not present, the license
# # is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
# #rSDK
# # This program is distributed in the hope that it will be useful, but
# # without any warranty; without even the implied warranty of merchantability
# # or fitness for a particular purpose. See the Common Public License for
# # full details.
# #
# 
from django.core.management.base import BaseCommand
from mint.django_rest.sdk_builder import rSDK
from xobj import xobj

# from mint.django_rest.sdk_builder.rSDKUtils import ClassStub

# from django.db.models.loading import cache
# from mint.django_rest.rbuilder.modellib.basemodels import XObjModel
# 
# ###### Sample Crap For Testing Purposes ######
#     
# PKGS_XML = \
# """
# <packages>
#     <data pid="1">my data</data>
#     <package pid="http://localhost/api/packages/1">
#         <name>Apache</name>
#         <description>Server</description>
#     </package>
#     <package pid="http://localhost/api/packages/2">
#         <name>Nano</name>
#         <description>Text Editor</description>
#     </package>
# </packages>
# """.strip()
# 
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

class TypedProperty(object):
    def __init__(self, name, type, default=None):
        """docstring for __init__"""
        self.name = '_' + name
        self.type = type
        self.default = type() if default is None else default
        
    def __get__(self, instance, cls):
        """docstring for __get__"""
        return getattr(instance, self.name, self.default) if instance else self
        
    def __set__(self, instance, value):
        """docstring for __set__"""
        if not isinstance(value, self.type):
            raise TypeError('Must be a %s' % self.type)
        setattr(instance, self.name, value)
        
    def __delete__(self, instance):
        """docstring for __delete__"""
        raise AttributeError("Can't delete attribute")

    def __call__(self, data=None, *args, **kwargs):
        return type(data)
        
# 
# from xobj.xobj import Document
from xobj.xobj import XObjMetadata
# 
class Url(xobj.XObj, rSDK.XObjMixin):
    tags = rSDK.Fields.TextField
    _xobj = XObjMetadata(tag='url', attributes={'tags':tags})

class Catalog(xobj.XObj, rSDK.XObjMixin):
    cid = rSDK.Fields.IntegerField
    url = [Url]
    _xobj = XObjMetadata(tag='Catalog', attributes={'cid':cid})

    
    
# 
# 
# class Data(xobj.XObj):
# 
#     
#     pid = rSDK.Fields.IntegerField
#     
# 
# class Package(xobj.XObj):
# 
#     pid = rSDK.Fields.URLField
#     name = rSDK.Fields.CharField
#     description = rSDK.Fields.TextField
#     _xobj = xobj.XObjMetadata(tag='package', attributes={'pid':pid})
# 
# 
# class Packages(xobj.XObj):
# 
#     
#     package = [Package]
#     data = Data
# 
# 
# 
# ##############################################
# 
# from xobj.xobj import Document
# 
# class Doc(Document):
#     __metaclass__ = rSDK.GetSetXMLAttrMeta
# 
# 
class Command(BaseCommand):
    help = "Generates python rSDK"

    def handle(self, *args, **options):
        """
        Generates Python SDK for REST API
        """
        # doc = xobj.parse(CXML, typeMap={'catalog':Catalog, 'url':Url})


        import pdb; pdb.set_trace()
        pass

#         # ##### For testing purposes only #####
#         doc = xobj.parse(CXML, typeMap={'catalog':Catalog, 'url':Url})  # pyflakes=ignore
#         import pdb; pdb.set_trace()
#         pass
#         
#         # # assignment works but shouldn't work (should throw assertion error)
#         # # doc.packages.package[0].name = u'new name' # FIXED
#         # 
#         # import pdb; pdb.set_trace()
#         # print doc.packages.data['pid']
#         # 
#         # # assignment fails but *should* fail (throws assertion error)
#         # # doc.packages.data.pid = 1
#         # 
#         # # assignment works and *should* work
#         # # doc.packages.data.pid = rSDK.Fields.IntegerField(1)
#         # 
#         # # assignment works but shouldn't work (should throw assertion error)
#         # # doc.packages.package[0].pid = 2 # FIXED
#         # 
#         # # notice that doc.toxml() leaves doc.packages.data empty
#         # # this is still most likely because Data is being registered
#         # # as a complexType.  Also is weird because if I leave the Data
#         # # class stub as empty, the data+id are correctly displayed.
#         # # This doesn't make sense because I don't have this problem
#         # # with Package.
#         # print doc.toxml()
#         # # notice that this should also fail, I should *not* be able to
#         # # assign an integer where instance of Data is needed.
#         # # doc.packages.data = 3 # FIXED
#         # 
#         # import pdb; pdb.set_trace()
#         # # however, the following works (and should work)
#         # doc.packages.data = Data('Hello World')
#         # # doc.toxml() correctly includes and renders doc.packages.data
#         # # however it is missing the id:
#         # import pdb; pdb.set_trace()
#         # print doc.toxml()
#         # # we can assign an id -- below does *not* work and shouldn't work
#         # # doc.packages.data.pid = 'X'
#         # # we can assign an id -- below *does* work and should work
#         # # doc.packages.data.pid = rSDK.Fields.IntegerField(1)
#         # p = Package()
#         # p.description = rSDK.Fields.TextField('a new package')
#         # p.pid = rSDK.Fields.URLField('http://helloworld.com/')
#         # p.name = rSDK.Fields.CharField('my new pkg')
#         # # doc.toxml() now renders what we expect to see
#         # doc.packages.package.append(p)
#         # 
#         # print doc.toxml()
#         # 
#         # print '\n'
#         # print '\n'
#         # 
#         # doc2 = xobj.parse(CXML, typeMap={'catalog':Catalog, 'url':Url})
#         # print doc2.toxml()
#         # import pdb; pdb.set_trace()
#         # pass
#         
#         # d = xobj.parse("<catalog />", typeMap={'catalog':Catalog, 'url':Url})
#         # u = Url('http://helloworld.com/')
#         # # u['tags'] = 'hello, greeting, common'
#         # import pdb; pdb.set_trace()
#         # pass
#         
#         
#         src = ClassStub(Packages)
#         print src.tosrc()
#         print '\n'
#         
#         class A(object):
#             pass
# 
#         class B(object):
#             pass
# 
#         class A2(object):
#             pass
# 
#         class C1(object):
#             list_fields = [A, A2]
# 
#         class C2(object):
#             list_fields = [C1, B]
# 
#         class C3(object):
#             list_fields = [A, C1]
# 
#         # ['A', 'A2', 'B', 'C1', 'C2']
# 
#         # def sortByListFields(*fields):
#         #     REGISTRY = []
#         #     for cls in fields:
#         #         listed = getattr(cls, 'list_fields', None)
#         #         if listed:
#         #             for c in listed:
#         #                 if cls not in REGISTRY:
#         #                     REGISTRY.append(cls)
#         #                 else:
#         #                     REGISTRY.remove(cls)
#         #                     REGISTRY.append(cls)
#         #         else:
#         #             REGISTRY.insert(0, cls)
#         #     return REGISTRY
#         
#         def sortByListFields(*fields):
#             registry = []
#             for cls in fields:
#                 listed = getattr(cls, 'list_fields', None)
#                 if listed:
#                     for c in listed:
#                         if cls not in registry:
#                             registry.append(cls)
#                         else:
#                             registry.remove(cls)
#                             registry.append(cls)
#                 elif cls in registry:
#                     continue
#                 else:
#                     registry.insert(0, cls)
#             return registry
#         
#         def findAllModels():
#              d = {}
#              for app in cache.get_apps():
#                  app_label = app.__name__.split('.')[-2]
#                  d[app_label] = app
#              return d
#         
#         ############## END ##################
#         print [c.__name__ for c in sortByListFields(B, A2, C1, A, C3, C2)]
#         # print [c.__name__ for c in sortByListFields(*sortByListFields(A, B, A2, C1, C2, C3))]
#         print ClassStub(C2).tosrc()
#         x = XObjModel()
#         models_dict = findAllModels()
#         packages = models_dict['packages']
#         # pObj = packages.Packages().serialize()
#         # pbj = packages.PackageBuildJob()
#         # serialized = pbj.serialize()
#         # import pdb; pdb.set_trace()
#         # pass

"dict(tag=%(tag))"
