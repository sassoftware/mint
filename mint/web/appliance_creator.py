from project import BaseProjectHandler
from mint.web.packagecreator import PackageCreatorMixin
from mint.web.decorators import ownerOnly, writersOnly, requiresAuth, \
        requiresAdmin, mailList, redirectHttp
from mint.web.fields import strFields, intFields, listFields, boolFields, dictFields

def start_apc_session(func):
    """ Starts a new apc session, if one isn't already set up
    """
    def apc_session_start_wrapper(s, *args, **kwargs):
        return func(s, *args, **kwargs)
    apc_session_start_wrapper.__wrapped_func__ = func
    return apc_session_start_wrapper

def check_session_version(func):
    def check_session_version_wrapper(s, *args, **kwargs):
        if s.session.get('versionId', None):
            return func(s, *args, **kwargs)
        else:
            s._addErrors('The product version is not set')
            s._predirect('landing', temporary=True)
    check_session_version_wrapper.__wrapped_func__ = func
    return check_session_version_wrapper

def check_repository_state(func):
    def check_repository_state_wrapper(s, *args, **kwargs):
        return func(s, *args, **kwargs)
    check_repository_state_wrapper.__wrapped_func__ = func
    return check_repository_state_wrapper

def output_handler(template = None, redirect=None):
    def output_handler_register(func):
        def output_handler_wrapper(s, *args, **kwargs):
            ret = func(s, *args, **kwargs)
            if redirect:
                #If we've been asked to redirect, do so and discard any output
                s._predirect(redirect, temporary=True)
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
    _projredirect = BaseProjectHandler._predirect
    def _predirect(self, path = "", temporary = False):
        self._redirect("http://%s%sproject/apc/%s/%s" % (self.cfg.projectSiteHost, self.cfg.basePath, self.project.hostname, path), temporary = temporary)

    @output_handler(redirect='landing')
    def index(self):
        return {}

    @start_apc_session
    @output_handler('landing')
    def landing(self):
        versions = self.project.getProductVersionList()
        if not versions:
            self._addErrors('You must create a product version before using appliance creator')
            self._predirect('editVersion', temporary=True)
        return dict(versions = versions, versionId=-1)

    @start_apc_session
    @output_handler(redirect='newPackage')
    @intFields(versionId = -1)
    def selectVersion(self, versionId):
        #TODO: Use the versionId to start an appliance creator session
        import epdb; epdb.serve()
        self.session['versionId'] = versionId
        self.session['appliance_creator_blarghh'] = {'key': ['value']}
        self.session.save()
        return dict(versionId=versionId, apcSessionHandle = 'blarghh')

    #@start_apc_session
    #@output_handler('componentSelection')
    #def selectComponents(self):
    #    return {}

    #@start_apc_session
    #@output_handler('blank')
    #def packageCreatorAdd(self):
    #    # Filter the list of packages by the active product version
    #    return {}

    @check_session_version
    @output_handler('createPackage')
    def newPackage(self):
        uploadDirectoryHandle = self.client.createPackageTmpDir()
        #lookup the productDefinition
        ver = self.client.getProductVersion(self.session['versionId'])
        return dict(uploadDirectoryHandle = uploadDirectoryHandle,
            message=None, versions = [], versionId = self.session['versionId'], prodVer=ver['name'],
            name=None, namespace=ver['namespace'], sessionHandle=None)

    @output_handler('uploadPackageFrame')
    @strFields(uploadId=None, fieldname=None)
    @boolFields(debug=False)
    def upload_iframe(self, uploadId, fieldname, debug):
        return {'uploadId': uploadId, 'fieldname': fieldname, 'project':
                self.project.hostname, 'debug': debug}

    @start_apc_session
    @output_handler('createPackageInterview')
    @strFields(uploadDirectoryHandle=None, upload_url='', sessionHandle='')
    @intFields(versionId=-1)
    def getPackageFactories(self, uploadDirectoryHandle, versionId, upload_url, sessionHandle):
        ret = self._getPackageFactories(uploadDirectoryHandle, versionId, sessionHandle, upload_url)
        return ret

    @start_apc_session
    @strFields(sessionHandle=None, factoryHandle=None)
    @output_handler('buildPackage')
    def savePackage(self, sessionHandle, factoryHandle, **kwargs):
        self.client.savePackage(sessionHandle, factoryHandle, kwargs)
        return dict(sessionHandle = sessionHandle, message = None)

    @check_session_version
    @start_apc_session
    @output_handler('blank')
    def build(self):
        return {}

