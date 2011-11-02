#
# Copyright (c) 2008 rPath, Inc.
# All rights reserved
#

from project import BaseProjectHandler
from mint.web import productversion
from mint.web.packagecreator import PackageCreatorMixin
from mint.web.decorators import writersOnly
from mint.web.fields import strFields, listFields, boolFields
from mint import mint_error

import itertools

def check_session(func):
    def check_session_version_wrapper(s, *args, **kwargs):
        #TODO: Check the session variable for the app sess handle
        return func(s, *args, **kwargs)
    check_session_version_wrapper.__wrapped_func__ = func
    return check_session_version_wrapper


#TODO: Start session needs to check the prod def for presence of images

# NOTE: there is also a list of "next steps" on the review page that should be
# updated when new things are added below

#Landing, component selection
WIZ_PACKCREAT   = 3.0
WIZ_EDIT_GROUP  = 4.0
WIZ_SELECT_PACKAGES   = 6.0
WIZ_REVIEW      = 7.0
WIZ_BUILD_GROUP = 8.0
WIZ_GENERATE    = 9.0

WIZ_MAINT_ONLY = () #(WIZ_REBASE, WIZ_EDIT_GROUP)

wizard_steps = {
    #constant:        (Text value, URL value)
    WIZ_PACKCREAT:  ("Create Packages", 'newPackage'),
    WIZ_SELECT_PACKAGES: ("Select Packages", 'selectPackages'),
    WIZ_EDIT_GROUP: ("Edit Appliance Contents", 'editApplianceGroup'),
    WIZ_REVIEW:     ("Review Appliance", 'reviewApplianceGroup'),
    WIZ_BUILD_GROUP:("Build Appliance", 'buildApplianceGroup'),
    WIZ_GENERATE:   ("Generate Images", 'generateImages'),
}


def collapsePkgList(pkglist, filterfunc):
    """Collapses a list of lists of packages to a single list of packages with no name duplicates.  Filters packages based on C{filterExpr}.
    """
    ret = {}
    for x in reversed(pkglist):
        for nvf in itertools.ifilter(filterfunc, x):
            ret[nvf[0]] = nvf
    return ret

def wizard_position(pos):
    """ Sets where in the wizard the method being called appears.  This method
    MUST be called before the output handler, e.g.
    
    @output_handler(template = 'blank')
    @wizard_position(WIZ_EDIT_GROUP)
    def land(self, ....):
    """
    def wizard_position_register(func):
        def wizard_position_wrapper(s, *args, **kwargs):
            ret = func(s, *args, **kwargs)
            if isinstance(ret, dict):
                # Stuff the position in the output dict, but only if it's not
                # already there
                if 'wizard_position' not in ret:
                    ret['wizard_position'] = pos
                if 'wizard_steps' not in ret:
                    ret['wizard_steps'] = wizard_steps
                if 'wizard_maint_steps' not in ret:
                    ret['wizard_maint_steps'] = WIZ_MAINT_ONLY
                if 'wizard_maint' not in ret:
                    ret['wizard_maint'] = s.session.get('appliance_creator_maintenance', False)
            return ret
        wizard_position_wrapper.__wrapped_func__ = func
        return wizard_position_wrapper
    return wizard_position_register

def output_handler(template = None, redirect=None):
    def output_handler_register(func):
        def output_handler_wrapper(s, *args, **kwargs):
            ret = func(s, *args, **kwargs)
            if redirect:
                #If we've been asked to redirect, do so and discard any output
                s._apcredirect(redirect, temporary=True)
            if type(ret) == str:
                return ret
            if template:
                assert type(ret) == dict, "You must return either a string or a dict"
                return s._write(template, **ret)
            else:
                return ret
        output_handler_wrapper.__wrapped_func__ = func
        return output_handler_wrapper
    return output_handler_register

class APCHandler(BaseProjectHandler, PackageCreatorMixin):
    def _getApplianceSessionHandle(self):
        return self.session.setdefault('apc_session_handle', {}).get(self.project.getId())

    def _setApplianceCreatorSession(self, sesH):
        self.session.setdefault('apc_session_handle', {})[self.project.getId()] = sesH
        self.session.save()
        return sesH

    def _apcredirect(self, path = "", temporary = False):
        self._redirectHttp('apc/%s/%s' % (self.project.hostname, path), temporary=temporary)

    @writersOnly
    @output_handler(redirect='landing')
    def index(self):
        """Convenience method to clear all session variables...for now"""
        for x in ('appliance_creator_maintenance', ):
            self.session.pop(x, None)
        self.session.save()

    @writersOnly
    @productversion.productVersionRequired
    @boolFields(maintain=False)
    @output_handler('landing')
    def landing(self, maintain):
        """All appliance creator actions must land here to set whether we're in
        maintenance mode or creation mode"""
        version = self.client.getProductVersion(self.currentVersion)
        pkglist = self.client.getPackageCreatorPackages(self.project.getId())
        pkgs = {}
        for n, info in pkglist.get(version['name'], {}).get(version['namespace'], {}).iteritems():
            #unlike the editApplianceGroup method, we only want the groups here
            if n.startswith('group-'):
                pkgs[n] = info
        return dict(message=None, groups=pkgs)

    @writersOnly
    @output_handler(redirect='newPackage')
    @boolFields(maintain=True)
    def startApplianceCreator(self, maintain):
        projectId = self.project.getId()
        # session is saved in the _setApplianceCreatorSession call
        self.session['appliance_creator_maintenance'] = maintain
        try:
            sesH = self.client.startApplianceCreatorSession(projectId,
                    self.currentVersion, maintain)[0]
        except mint_error.NoImagesDefined:
            version = self.client.getProductVersion(self.currentVersion)
            self._addErrors("No images have been defined for version: %s" % \
                    version.get('name'))
            self._predirect('editVersion?id=%d' % self.currentVersion,
                    temporary=True)

        except mint_error.OldProductDefinition:
            version = self.client.getProductVersion(self.currentVersion)
            self._addErrors("Update to the latest appliance platform to continue.")
            self._predirect('editVersion?id=%d' % self.currentVersion,
                    temporary=True)

        self._setApplianceCreatorSession(sesH)

    @writersOnly
    @output_handler('createPackageWiz')
    @wizard_position(WIZ_PACKCREAT)
    def newPackage(self):
        uploadDirectoryHandle = self.client.createPackageTmpDir()
        #lookup the productDefinition
        return dict(message = '', uploadDirectoryHandle =
            uploadDirectoryHandle, sessionHandle=None, name=None)

    @writersOnly
    @strFields(uploadId=None, fieldname=None)
    @boolFields(debug=False)
    @output_handler('uploadPackageFrame')
    @wizard_position(WIZ_PACKCREAT)
    def upload_iframe(self, uploadId, fieldname, debug):
        return {'uploadId': uploadId, 'fieldname': fieldname, 'project':
                self.project.hostname, 'debug': debug}

    @writersOnly
    @strFields(uploadDirectoryHandle=None, upload_url='', sessionHandle='')
    @output_handler('createPackageInterviewWiz')
    @wizard_position(WIZ_PACKCREAT)
    def getPackageFactories(self, uploadDirectoryHandle, upload_url, sessionHandle):
        ret = self._getPackageFactories(uploadDirectoryHandle, self.currentVersion, sessionHandle, upload_url)
        return ret

    @writersOnly
    @strFields(sessionHandle=None, factoryHandle=None, recipeContents='')
    @boolFields(useOverrideRecipe=False)
    @output_handler('buildPackageWiz')
    @wizard_position(WIZ_PACKCREAT)
    def savePackage(self, sessionHandle, factoryHandle, recipeContents, useOverrideRecipe, **kwargs):
        if not useOverrideRecipe:
            recipeContents = ''
        self.client.savePackageCreatorRecipe(sessionHandle, recipeContents)
        pkg = self.client.savePackage(sessionHandle, factoryHandle, kwargs)
        if pkg:
            # This needs to be more sophisticated, for now we just try to add
            # it.  If the package fails to build, an error will occur during
            # cooking if the user does not remove it in the edit group page
            self.client.addApplianceTrove(self._getApplianceSessionHandle(), pkg)
        return dict(sessionHandle = sessionHandle, message = None)

    @writersOnly
    @output_handler('packageListWiz')
    def packageList(self):
        def filtercomponents(nvf):
            if ':' in nvf[0]:
                return False
            return True

        import kid
        from os.path import join
        sesH = self._getApplianceSessionHandle()
        pkgs = self.client.getAvailablePackages(sesH)
        pkgs = collapsePkgList(pkgs, filtercomponents)
        path = join(self.cfg.templatePath, "packageListWiz.kid")
        template = kid.load_template(path)

        t = template.Template(packageList=pkgs)
        t.assume_encoding = 'latin1'
        self.req.content_type = "text/html"
        ret = t.serialize(encoding = "utf-8", output = "html-strict")

        # lop off the doctype declaration since kid can't do it in 0.9.1
        return ret[ret.find('>')+1:]

    @writersOnly
    @output_handler('selectPackagesShellWiz')
    @wizard_position(WIZ_SELECT_PACKAGES)
    def selectPackages(self):
        return dict(message=None)

    @writersOnly
    @output_handler(redirect='editApplianceGroup')
    @listFields(str, troves=[])
    def processSelectPackages(self, troves):
        self.client.addApplianceTroves(self._getApplianceSessionHandle(), troves)

    @writersOnly
    @output_handler('editGroupWiz')
    @wizard_position(WIZ_EDIT_GROUP)
    def editApplianceGroup(self):
        version = self.client.getProductVersion(self.currentVersion)
        sesH = self._getApplianceSessionHandle()
        pkgs = self.client.listApplianceTroves(self.project.getId(), sesH)
        isDefault, recipeContents = self.client.getPackageCreatorRecipe(sesH)

        return dict(message=None, packageList = pkgs,
                recipeContents = recipeContents,
                useOverrideRecipe = not isDefault)

    @writersOnly
    @output_handler(redirect="reviewApplianceGroup")
    @listFields(str, troves=[])
    @strFields(recipeContents='')
    @boolFields(useOverrideRecipe=False)
    def processEditApplianceGroup(self, troves, recipeContents, useOverrideRecipe):
        sesH = self._getApplianceSessionHandle()
        self.client.setApplianceTroves(sesH, troves)
        if not useOverrideRecipe:
            recipeContents = ''
        self.client.savePackageCreatorRecipe(sesH, recipeContents)

    @writersOnly
    @output_handler('reviewGroupWiz')
    @wizard_position(WIZ_REVIEW)
    def reviewApplianceGroup(self):
        explicitTroves = self.client.listApplianceTroves(self.project.getId(), self._getApplianceSessionHandle())
        return dict(message=None, explicitTroves = explicitTroves)

    @writersOnly
    @output_handler(redirect="buildGroupStatus")
    def buildApplianceGroup(self):
        #Save the group, and kick off the build.  Javascript to watch
        sesH = self._getApplianceSessionHandle()
        buildId = self.client.makeApplianceTrove(sesH)

    @writersOnly
    @output_handler('buildGroupWiz')
    @wizard_position(WIZ_BUILD_GROUP)
    def buildGroupStatus(self):
        sesH = self._getApplianceSessionHandle()
        return dict(message=None, applianceSessionHandle=sesH)

    @writersOnly
    @output_handler(redirect="imageBuildStatus")
    def generateImages(self):
        # Kick off a build on the devel stage
        buildIds = self.client.newBuildsFromProductDefinition(self.currentVersion, 'Development', True)
        self.session['last_image_set'] = buildIds
        self.session.save()

    @writersOnly
    @output_handler('generateImagesWiz')
    @wizard_position(WIZ_GENERATE)
    def imageBuildStatus(self):
        buildIds = self.session.get('last_image_set', [])
        builds = {}
        for bid in buildIds:
            builds[bid] = self.client.getBuild(bid)
        return {'builds': builds}
