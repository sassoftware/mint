#
# Copyright (c) 2008 rPath, Inc.
# All rights reserved
#

from mint.mint_error import MintError
from mint.web.fields import strFields
from mint.web.decorators import writersOnly

class PackageCreatorMixin(object):
    """Must be mixed with a ProjectHandler based class"""

    def _getPackageFactories(self, uploadDirectoryHandle, versionId, sessionHandle, upload_url):
        isDefault = False
        recipeContents = ''
        if sessionHandle:
            editing = True
        else:
            editing = False
        try:
            sessionHandle, factories, prevChoices = self.client.getPackageFactories(self.project.getId(), uploadDirectoryHandle, versionId, sessionHandle, upload_url)
            isDefault, recipeContents = self.client.getPackageCreatorRecipe(sessionHandle)
        except MintError, e:
            self._addErrors(str(e))
            self._predirect('newPackage', temporary=True)
        if not factories:
            self._addErrors("Update to the latest appliance platform to continue.")
            self._predirect('editVersion?id=%d' % self.currentVersion,
                    temporary=True)

        return {'editing': editing, 'sessionHandle': sessionHandle, 'factories': factories, 'prevChoices': prevChoices,
                'recipeContents': recipeContents, 'useOverrideRecipe': not isDefault}

    @writersOnly
    @strFields(sessionHandle=None)
    def getPackageBuildLogs(self, auth, sessionHandle):
        try:
            logs = self.client.getPackageBuildLogs(sessionHandle)
        except MintError, e:
            self._addErrors("Build logs are not available for this build: %s" % str(e))
            self._predirect('index', temporary=True)

        self.req.content_type = 'text/plain'
        return logs

