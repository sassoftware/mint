#
# Copyright (c) 2008 rPath, Inc.
# All rights reserved
#

from project import BaseProjectHandler
from mint.web import productversion
from mint.web.packagecreator import PackageCreatorMixin
from mint.web.decorators import ownerOnly, writersOnly, requiresAuth, \
        requiresAdmin, mailList, redirectHttp
from mint.web.fields import strFields, intFields, listFields, boolFields, dictFields

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
WIZ_LAND        = 1.0
WIZ_REBASE      = 2.0
WIZ_COMPONENTS  = 3.0
WIZ_SELECT_PACK = 4.0
WIZ_PACKCREAT   = 5.0
WIZ_EDIT_GROUP  = 6.0
WIZ_REVIEW      = 7.0
WIZ_BUILD_GROUP = 8.0
WIZ_GENERATE    = 9.0
WIZ_DEPLOY      = 10.0

WIZ_MAINT_ONLY = () #(WIZ_REBASE, WIZ_EDIT_GROUP)

wizard_steps = {
    #constant:        (Text value, URL value)
    WIZ_LAND:       ("Select Product Version", 'landing'),
   #WIZ_REBASE:     ("Rebase", 'rebase'),
   #WIZ_COMPONENTS: ("Select Application Stack", "selectComponents"),
   #WIZ_SELECT_PACK:("Select Appliance Packages", "packageCreatorAdd"),
    WIZ_PACKCREAT:  ("Create Packages", 'newPackage'),
    WIZ_EDIT_GROUP: ("Edit Appliance Contents", 'editGroup'),
    WIZ_REVIEW:     ("Review Appliance", 'review'),
    WIZ_BUILD_GROUP:("Build Appliance", 'buildGroup'),
    WIZ_GENERATE:   ("Generate Images", 'build'),
    WIZ_DEPLOY:     ("Deploy Images", 'deploy'),
}

def wizard_position(pos):
    """ Sets where in the wizard the method being called appears.  This method
    MUST be called before the output handler, e.g.
    
    @output_handler(template = 'blank')
    @wizard_position(WIZ_LAND)
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
        self._redirect("http://%s%sapc/%s/%s" % (self.cfg.projectSiteHost, self.cfg.basePath, self.project.hostname, path), temporary = temporary)

    @output_handler(redirect='landing')
    def index(self):
        """Convenience method to clear all session variables...for now"""
        for x in ('appliance_creator_maintenance', ):
            self.session.pop(x, None)
        self.session.save()

    @productversion.productVersionRequired
    @boolFields(maintain=False)
    @output_handler('landing')
    def landing(self, maintain):
        """All appliance creator actions must land here to set whether we're in
        maintenance mode or creation mode"""
        self.session['appliance_creator_maintenance'] = maintain
        self.session.save()
        return dict(message=None)

    @output_handler(redirect='newPackage')
    def startApplianceCreator(self):
        projectId = self.project.getId()
        sesH = self.client.startApplianceCreatorSession(projectId, self.currentVersion, False)
        self._setApplianceCreatorSession(sesH)

    @output_handler('createPackageWiz')
    @wizard_position(WIZ_PACKCREAT)
    def newPackage(self):
        uploadDirectoryHandle = self.client.createPackageTmpDir()
        #lookup the productDefinition
        return dict(message = '', uploadDirectoryHandle =
            uploadDirectoryHandle, sessionHandle=None, name=None)

    @strFields(uploadId=None, fieldname=None)
    @boolFields(debug=False)
    @output_handler('uploadPackageFrame')
    @wizard_position(WIZ_PACKCREAT)
    def upload_iframe(self, uploadId, fieldname, debug):
        return {'uploadId': uploadId, 'fieldname': fieldname, 'project':
                self.project.hostname, 'debug': debug}

    @strFields(uploadDirectoryHandle=None, upload_url='', sessionHandle='')
    @output_handler('createPackageInterviewWiz')
    @wizard_position(WIZ_PACKCREAT)
    def getPackageFactories(self, uploadDirectoryHandle, upload_url, sessionHandle):
        ret = self._getPackageFactories(uploadDirectoryHandle, self.currentVersion, sessionHandle, upload_url)
        return ret

    @strFields(sessionHandle=None, factoryHandle=None)
    @output_handler('buildPackageWiz')
    @wizard_position(WIZ_PACKCREAT)
    def savePackage(self, sessionHandle, factoryHandle, **kwargs):
        self.client.savePackage(sessionHandle, factoryHandle, kwargs)
        return dict(sessionHandle = sessionHandle, message = None)

    @output_handler('editGroupWiz')
    @wizard_position(WIZ_EDIT_GROUP)
    def editGroup(self):
        ### TODO: Flush this out
        version = self.client.getProductVersion(self.currentVersion)
        sesH = self._getApplianceSessionHandle()
        pkglist = self.client.getPackageCreatorPackages(self.project.getId())
        pkgs = []
        for n, info in pkglist.get(version['name'], {}).get(version['namespace'], {}).iteritems():
            if not n.startswith('group-'):
                pkgs[n] = info
        selected = self.client.listApplianceTroves(sesH)
        return dict(message=None, packageList = pkgs, selected = selected)

    @output_handler(redirect="review")
    @listFields(str, troves=[])
    def processEditGroup(self, troves):
        self.client.setApplianceTroves(self._getApplianceSessionHandle(), troves)

    @output_handler('reviewGroupWiz')
    @wizard_position(WIZ_REVIEW)
    def review(self):
        explicitTroves = self.client.listApplianceTroves(self._getApplianceSessionHandle())
        return dict(message=None, explicitTroves = explicitTroves)

    @output_handler('buildGroupWiz')
    @wizard_position(WIZ_BUILD_GROUP)
    def buildGroup(self):
        #Save the group, and kick off the build.  Javascript to watch
        sesH = self._getApplianceSessionHandle()
        buildId = self.client.makeApplianceTrove(sesH)
        return dict(message=None, applianceSessionHandle=sesH)

    def generateImages(self):
        # Kick off a build on the devel stage
        buildIds = self.client.newBuildsFromProductDefinition(self.currentVersion, 'Development', True)
        self._setInfo("Builds created.")
        self._predirect('builds')
