#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from mint.django_rest.deco import return_xml, requires
from mint.django_rest.rbuilder import service
from django.http import HttpResponse

class BasePackageService(service.BaseService):
    pass

class PackagesService(BasePackageService):
    """docstring for PackageService"""

    @return_xml
    def rest_GET(self, request):
        """docstring for rest_GET"""
        return self.get()

    def get(self):
        return self.mgr.getPackages()

    # access.admin
    @requires('package')
    @return_xml
    def rest_POST(self, request, package):
        """docstring for rest_POST"""
        return self.mgr.addPackage(package)

class PackageService(BasePackageService):
    """docstring for PackageService"""

    @return_xml
    def rest_GET(self, request, package_id):
        """docstring for rest_GET"""
        return self.get(package_id)

    def get(self, package_id):
        return self.mgr.getPackage(package_id)

    # @access.admin
    @requires('package')
    @return_xml
    def rest_PUT(self, request, package_id, package):
        """docstring for rest_PUT"""
        return self.mgr.updatePackage(package_id, package)

    # @access.admin   
    def rest_DELETE(self, request, package_id):
        """docstring for rest_DELETE"""
        self.mgr.deletePackage(package_id)
        response = HttpResponse(status=204)
        return response
