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

api = connect('http://server/api/')

# GET
api.GET('/packages/') # get all packages
api.GET('/packages/1') # get first package

# POST
pkg = sdk.Models.package.Package() # create
pkg.name = 'xobj'
pkg.description = 'A python to xml serialization library'
api.POST('/packages/', pkg)

# PUT
pkg2 = api.GET('/packages/2')
pkg2.name = 'Package 2 Renamed'
api.PUT('/packages/2', pkg2)

# DELETE
api.DELETE('/packages/2')

# Navigate
pkgs = api.GET('/packages/')
for p in pkgs.package:
    print 'id: %s' % p['id']
    print 'name: %s, description: %s' % (p.name, p.description)
    
# Validate
pkg = api.GET('/packages/1')
isinstance(pkg['id'], sdk.Fields.URLField) # is True
pkg['id'] = 'bad id' # throws an assertion error
pkg['id'] = 'http://validid.com/' # works