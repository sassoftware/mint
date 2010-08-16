
from mint_test import fixtures

from mint.django_rest import middleware

class DjangoMiddlewareTest(fixtures.FixturedUnitTest):

    def setUp(self):    
        pass

    def tearDown(self):
        pass

    def testCommentXSL(self):
        commentMiddleware = middleware.AddCommentsMiddleware()

        assert(commentMiddleware.useXForm == True)
        
        
