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

class appengine::rmake {

    service { 'rmake-messagebus':       ensure => running, enable => true }
    service { 'rmake':                  ensure => running, enable => true, require => Service['rmake-messagebus'], notify => Service['rmake-node'] }
    service { 'rmake-node':             ensure => running, enable => true, require => Service['rmake'] }

    rbuilder_project { 'rmake-repository':
        ensure => present,
        hidden => true,
        display_name => "rMake Repository",
        description => "Please consider the contents of this product's repository to be for REFERENCE PURPOSES ONLY.\nThis product's repository is used by the rMake server running on this rBuilder for building packages and groups with Package Creator and Appliance Creator. This product is for the internal use of the rBuilder server. Do not attempt to manipulate the contents of this repository. Do not shadow, clone or otherwise reference any packages or components from this repository. This product can be reset at any time, which would lead to errors in anything that references the contents of this product's repository.",
        notify => Rbuilder_rmakeuser['rmake'],
    }

    rbuilder_rmakeuser { 'rmake':
        notify => Service['rmake'],
        ensure => present,
    }
}
