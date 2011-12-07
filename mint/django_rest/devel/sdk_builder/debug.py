# #
# # Copyright (c) 2011 rPath, Inc.
# #
# # This program is distributed under the terms of the Common Public License,
# # version 1.0. A copy of this license should have been distributed with this
# # source file in a file called LICENSE. If it is not present, the license
# # is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
# #
# # This program is distributed in the hope that it will be useful, but
# # without any warranty; without even the implied warranty of merchantability
# # or fitness for a particular purpose. See the Common Public License for
# # full details.
# #
# 
# #
# # Copyright (c) 2011 rPath, Inc.
# #
# # This program is distributed under the terms of the Common Public License,
# # version 1.0. A copy of this license should have been distributed with this
# # source file in a file called LICENSE. If it is not present, the license
# # is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
# #
# # This program is distributed in the hope that it will be useful, but
# # without any warranty; without even the implied warranty of merchantability
# # or fitness for a particular purpose. See the Common Public License for
# # full details.
# #
# 
# import inspect
# from rsdk.packages import TYPEMAP as PKGSMAP
# from rsdk.packages import Package, Packages
# from rsdk.inventory import TYPEMAP as INVMAP
# from rsdk.rbuilder import Users
# from rsdk.sdk import toCamelCaps, SDKModelMeta
# from rsdk import connect
# from xobj import xobj
# from rsdk.Fields import CharField
# from rsdk import rebind
# 
#      
# class MyUsers(Users):
#     """
#     Users class with custom __unicode__ and __str__
#     """
#     
#     def __init__(self, *args, **kwargs):
#         Users.__init__(self, **kwargs)
#         if args and 'username' not in kwargs:
#             self.username = args[0]
#         
#     def __unicode__(self):
#         return unicode(self.username)
#         
#     def __str__(self):
#         return str(self.username)
# 
# 
# 
# p = Package()
# doc = xobj.Document()
# doc.package = p
# print doc.toxml()
# 
# try:
#     Package(name=1)
# except:
#     print 'Package(name=1) validation error'
# 
# try:
#     p = Package()
#     p.name = 'nano'
#     p.name = 1
# except:
#     print 'p.name = 1 validation error'    
# 
# print '\n'
# 
# print p.__dict__.keys()
# 
# api = connect('http://172.16.49.132:8000/api/')
# pkg1 = api.GET('packages/1', PKGSMAP)
# 
# print pkg1.toxml()
# 
# 
# rebind(MyUsers, PKGSMAP)
# 
# print '\n'
# 
# try:
#     Package(name=1)
# except:
#     print 'rebound Package(name=1) validation error'
# 
# try:
#     p = Package()
#     p.name = 'nano'
#     p.name = 1
# except:
#     print 'rebound p.name = 1 validation error'
# 
# print '\n'
# print '\n'
# cb = PKGSMAP['package'].created_by('admin')
# cb2 = PKGSMAP['package'].created_by(username='admin')
# 
# 
# print cb.__dict__.keys()
# print cb
# 
# print '\n doc2'
# doc2 = xobj.Document()
# doc2.users = cb
# cb.fullname = 'dan cohn'
# print doc2.toxml()
# 
# print '\n'
# 
# pkg1 = api.GET('packages/1', PKGSMAP)
# print pkg1.toxml()
# 
# u = MyUsers(username='admin', fullname='Dan Cohn')
# print u
# print u.fullname
# print u.__dict__.keys()
# print type(PKGSMAP['package'].created_by)
# 
# try:
#     u.username = 1
# except:
#     print 'rebound u.username=1 validation error'
# 
# try:
#     pkg1.package.created_by.username = 1
# except:
#     print 'rebound username=1 validation error'
# 
# pkg2 = api.GET('packages/2', PKGSMAP)
# print pkg2.toxml()
# print 'username ', pkg2.package.created_by.username
# 
# PKGSXML = \
# """
# <package id="http://172.16.49.132:8000/api/packages/2">
#   <modified_date>2011-03-23T19:13:01+00:00</modified_date>
#   <modified_by href="http://172.16.49.132:8000/api/inventory/users/1">admin</modified_by>
#   <description>Omni Billing System</description>
#   <package_versions id="http://172.16.49.132:8000/api/packages/2/package_versions"/>
#   <created_by href="http://172.16.49.132:8000/api/inventory/users/1">admin</created_by>
#   <package_id>2</package_id>
#   <created_date>2011-03-23T19:13:01+00:00</created_date>
#   <name>omni</name>
# </package>
# """.strip()
# 
# psample = xobj.parse(PKGSXML, typeMap=PKGSMAP)
# print psample.toxml()
# 
# from rsdk import purgeByType, purgeByNode
# 
# purgeByType(psample, Users)
# print psample.toxml()
# 
# 
# purgeByNode(psample, 'created_by')
# print psample.toxml()
# 
# import pdb; pdb.set_trace()
# pass
