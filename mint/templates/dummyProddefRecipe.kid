<?xml version='1.0' encoding='UTF-8'?>
<plain xmlns:py="http://purl.org/kid/ns#">
# vim: ts=4 sw=4 expandtab ai
#
# Copyright (c) 2008 rPath, Inc.
# This file is distributed under the terms of the MIT License.
# A copy is available at http://www.rpath.com/permanent/mit-license.html
#
# Dummy recipe for Product Definition; it only exists to allow a user
# to use cvc checkin/checkout from the command line. Do not edit!
#
class ${projectName.capitalize()}ProductDefintion(PackageRecipe):
    name = 'proddef'
    version = '1.0'

    def setup(r):
        r.addSource('proddef.xml')
</plain>
