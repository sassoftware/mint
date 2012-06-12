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

##############################################################################
Client Side Features:
##############################################################################

* Able to initialize via keyword args OR attribute assignment,
        p = Package(name='Nano')
                or
        p = Package(); p.name = 'Nano'

* For classes containing subelements (such as Packages), are be able 
  to initialize via keyword arguments as well as attribute assignment,
        p = Package(name='Nano'); pkgs = Packages(package=[p])
                or
        p = Package(name='Nano'); pkgs = Packages(); pkgs.package = [p]

* Validation works for both keyword arguments and attribute assignment,
        p = Package(name=1) # throws sdk.ValidationError
                or
        p = Package(); p.name = 1 # throws sdk.ValidationError
        (where name is a CharField which means it only accepts str or unicode)

* Subclass models,
        from rsdk.rbuilder import Users, TYPEMAP
        
        class MyUsers(Users):
            def __init__(self, *args, **kwargs):
                if args and not kwargs:
                    self.username = args[0]
            
            def __unicode__(self):
                return self.username
                
        followed by,
        
        rebind(MyUsers, TYPEMAP)

* Serialize python to xml using xobj,
        doc = xobj.Document()
        doc.package = Package(name='Nano', description='Text Editor')
        print doc.toxml()

* Deserialize xml to python using xobj
        doc = xobj.parse(packages_xml, typeMap=TYPEMAP)
        print doc.packages.package[0].name

##############################################################################
TODO:
##############################################################################
finish validators
clean up documentation