from restlib import response

from mint.rest.api import base
from mint.rest.middleware import auth

class RegistrationController(base.BaseController):

    @auth.noDisablement
    @auth.public
    def update(self, request):
        self.db.setRegistration(request.read())
        return response.Response('')

    @auth.noDisablement
    @auth.public
    def index(self, request):
        form = self.db.getRegistrationForm()
        if form:
            return response.Response(form)
        else:
            return response.Response(content='Registration form not available.',
                    content_type='text/plain', status=500)
