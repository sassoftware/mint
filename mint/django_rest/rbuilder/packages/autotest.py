from mint.django_rest.rbuilder.inventory.tests import XMLTestCase
from mint.django_rest.urls import urlpatterns
from mint.django_rest.rbuilder.packages import models

class test(object):
    """
    Class decorator that automatically generates
    base unittests for a particular view.
    """

    class RestTestCase(XMLTestCase):

        def setUp(self):
            XMLTestCase.setUp(self)

        def testGET(self):
            """
            Gets value from db, then from a GET request.
            Afterwards compares the results
            """
            

        def testPOST(self):
            """
            Adds content to db via a POST then checks
            that the data has been added
            """
            pass

        def testPUT(self):
            """
            Picks some data in the database, updates
            it with a PUT, then checks that the updated
            values match.
            """
            pass

        def testDELETE(self):
            """
            Find some data already in db, do a DELETE
            then check that the data is deleted
            """
            pass

    def __new__(cls, view):
        test.view = view
        view.test = test.RestTestCase
        return view

    @staticmethod
    def getModelsFromView(cls, view):
        """Get model(s) corresponding to a view"""
        models_dict = {}
        for u in urlpatterns:
            if isinstance(u.callback.__class__, view):
                models_dict[u.name] = models.__dict__[u.name]
        return models_dict