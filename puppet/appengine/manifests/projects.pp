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

class appengine::projects {

    rbuilder_project { 'pdt':
        ensure                  => present,
        external                => true,
        display_name            => "SAS Infrastructure",
        repository_hostname     => "pdt.cny.sas.com",
        upstream_url            => $appengine::upstream_url,
    }

    rbuilder_project { 'vdk':
        ensure                  => present,
        external                => true,
        display_name            => "SAS vApp Development Kit",
        repository_hostname     => "vdk.cny.sas.com",
        upstream_url            => $appengine::upstream_url,
    }

    exec { '/usr/share/rbuilder/scripts/repository-sync': }

    Rbuilder_project <| |> -> Exec['/usr/share/rbuilder/scripts/repository-sync']

}
