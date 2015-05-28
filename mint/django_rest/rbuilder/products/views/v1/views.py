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


from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.projects import models as projectmodels

class MajorVersionService(service.BaseAuthService):

    def get(self, request, short_name, version):
        """
        XXX defunct for now
        """
        modifiers = ['platform', 'platform_version', 'definition', 'image_type_definitions',
                     'image_definitions', 'images', 'source_group']
        project = projectmodels.Project.objects.get(short_name=short_name)
        project_version = projectmodels.ProjectVersion.objects.get(project=project)
        for m in modifiers:
            url = r'%(host)s/api/products/%(short_name)s/versions/%(version)s/%(modifier)s/'\
                    % dict(host= 'http://' + request.get_host(), short_name=short_name, version=version, modifier=m)
            setattr(project_version, m, url)
        return project_version
