#
# Copyright (c) 2008 rPath, Inc.
#
# All rights reserved
#

from mint.web.fields import strFields, intFields, listFields, boolFields, dictFields

def productVersionRequired(func):
    def prodVerReqWrap(s, *args, **kwargs):
        if s.currentVersion is None:
            s._addErrors("You must have a version selected before you can visit this page.  Select one from the left menu before trying again.")
            s._predirect('', temporary=True)
        return func(s, *args, **kwargs)
    prodVerReqWrap.__wrapped_func__ = func
    return prodVerReqWrap

class ProductVersionView(object):
    """ Simple mixin class to collect the bits and pieces required to show a
    version view of a product workspace.  This assumes a webhandler based
    class. """

    def setupView(self):
        if not self.project.external:
            self.versions = self.client.getProductVersionListForProduct(
                self.project.id)
            self.currentVersion = self._getCurrentProductVersion()
        else:
            self.versions = []
            self.currentVersion = None

    def _getCurrentProductVersion(self):
        return self.session.setdefault('currentVersion', {}).get(self.project.getId())

    def _setCurrentProductVersion(self, versionId):
        if versionId < 0:
            self.session.setdefault('currentVersion', {}).pop(self.project.getId(), None)
        else:
            self.session.setdefault('currentVersion', {})[self.project.getId()] = versionId
        self.session.save()

    @intFields(versionId=-1)
    @strFields(redirect_to = None)
    def setProductVersion(self, versionId, redirect_to):
        self._setCurrentProductVersion(versionId)
        self.session.save()
        self._redirect(redirect_to, temporary=True)


