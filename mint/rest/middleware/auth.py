import base64

from restlib.response import Response
from mint import config
from mint import shimclient

class AuthenticationCallback(object):

    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db = db

    def getAuth(self, request):
        if not 'Authorization' in request.headers:
            return None
        type, user_pass = request.headers['Authorization'].split(' ', 1)
        user_name, password = base64.decodestring(user_pass).split(':', 1)
        return (user_name, password)

    def processRequest(self, request):
        auth = self.getAuth(request)
        if not auth:
            # require authentication
            return Response(status=401, 
                 headers={'WWW-Authenticate' : 'Basic realm="rBuilder"'})
        request.auth = auth
        mintClient = shimclient.ShimMintClient(self.cfg, auth)
        mintAuth = mintClient.checkAuth()
        if not mintAuth.authorized:
            return Response(status=403)
        request.mintClient = mintClient
        request.mintAuth = mintAuth
        self.db.setAuth(mintAuth.userId, mintAuth.admin, mintAuth.username)
