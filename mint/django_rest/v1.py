#
# Copyright (c) rPath, Inc.
#

from django.conf.urls.defaults import patterns, include

from mint.django_rest.rbuilder.targets.views.v1 import views as targetsviews

from mint.django_rest import urls

# TODO: move this?
handler404 = 'mint.django_rest.handler.handler404'
handler500 = 'mint.django_rest.handler.handler500'

URL = urls.URLRegistry.URL

# FIXME: view names will need the version as a prefix or postfix so resolvers
# can support v2, can update URL function to know & append context

urlpatterns = patterns('',

    (r'^/images',
     include('mint.django_rest.rbuilder.images.views.v1.urls')),

    (r'^/image_types',
     include('mint.django_rest.rbuilder.images.views.v1.urls_image_types')),

    (r'^/inventory',
     include('mint.django_rest.rbuilder.inventory.views.v1.urls')),

    (r'^/jobs',
     include('mint.django_rest.rbuilder.jobs.views.v1.urls')),

    (r'^/job_states',
     include('mint.django_rest.rbuilder.jobs.views.v1.urls_job_states')),

    (r'^/query_sets',
     include('mint.django_rest.rbuilder.querysets.views.v1.urls')),

    (r'^/products',
     include('mint.django_rest.rbuilder.products.views.v1.urls')),

    (r'^/favorites',
     include('mint.django_rest.rbuilder.favorites.views.v1.urls')),

    (r'^/project_branches',
     include('mint.django_rest.rbuilder.projects.views.v1.urls_pb')),

    (r'^/project_branch_stages',
     include('mint.django_rest.rbuilder.projects.views.v1.urls_pbs')),

    (r'^/projects',
     include('mint.django_rest.rbuilder.projects.views.v1.urls')),

    (r'^/packages',
     include('mint.django_rest.rbuilder.packageindex.views.v1.urls')),

    (r'^/session',
     include('mint.django_rest.rbuilder.session.views.v1.urls')),

    (r'^/users',
     include('mint.django_rest.rbuilder.users.views.v1.urls')),

    (r'^/platforms',
     include('mint.django_rest.rbuilder.platforms.views.v1.urls')),

    (r'^/rbac',
     include('mint.django_rest.rbuilder.rbac.views.v1.urls')),

    (r'^/module_hooks',
     include('mint.django_rest.rbuilder.modulehooks.views.v1.urls')),

    (r'^/targets',
     include('mint.django_rest.rbuilder.targets.views.v1.urls')),

    (r'^/target_jobs',
     include('mint.django_rest.rbuilder.targets.views.v1.urls_target_jobs')),

    (r'^/target_types',
     include('mint.django_rest.rbuilder.targets.views.v1.urls_target_types')),

    (r'^/target_type_jobs',
     include('mint.django_rest.rbuilder.targets.views.v1.urls_target_type_jobs')),
                       
    # Generic descriptors for creating resources
    # FIXME -- migrate to new structure
    URL(r'/descriptors/targets/create/?$',
        targetsviews.DescriptorTargetsCreationService(),
        name='DescriptorsTargetsCreate'),
)
