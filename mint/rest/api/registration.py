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
        form = self.db.getRegistrationForm(request)
        return response.Response(form)
