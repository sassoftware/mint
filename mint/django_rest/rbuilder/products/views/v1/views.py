#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
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

