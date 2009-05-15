from restlib import response

from mint.rest.api import base, models
from mint.rest.middleware import auth

class RegistrationController(base.BaseController):
    urls = {'form': dict(GET='getForm')}

    @auth.noDisablement
    @auth.public
    def index(self, request):
        return models.RegistrationStub()

    @auth.noDisablement
    @auth.public
    def update(self, request):
        self.db.setRegistration(request.read())
        return response.Response('')

    @auth.noDisablement
    @auth.public
    def getForm(self, request):
        form = self.db.getRegistrationForm()
        if form:
            return response.Response(form, content_type='text/xml')
        else:
            return response.Response(content='Registration form not available.',
                    content_type='text/plain', status=500)
