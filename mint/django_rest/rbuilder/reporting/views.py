from mint.django_rest.rbuilder.xobj_responder import xobjResponder
from mint.django_rest.rbuilder.reporting.models import ReportType, ReportTypes

from xobj import xobj

from django.http import HttpResponse
from django_restapi.resource import Resource

class ReportTypeView(Resource):

    # Handle GET methods
    def read(self, request):
        queryset = []
        for type in _reporttypes.values():
            rt = ReportType()
            for attr in type.items():              
                setattr(rt, attr[0], attr[1])
            
            rt.populateElements(request)    
            queryset.append(rt)
        
        obj = ReportTypes()
        obj.addQueryset(queryset)
        return HttpResponse(xobj.toxml(obj, obj.__class__.__name__), "text/plain")     

# FIXME:  This is tied to the reportdispatcher.py code        
_reporttypes = {
    'imagesReport': { 'uri' : 'imagesReport',
                      'name' : 'Image Creation Timeline',
                      'description': 'Show the number of images created for a product by different aggregations',
                      'timecreated': 1240934903,
                      'enabled' : True,
                    },
    'systemUpdateCheck' : { 'uri' : 'systemUpdateCheck',
                               'name' : 'System Update Check',
                               'description' : 'Show the number of systems checking for updates from this rBuilder Appliance',
                               'timecreated' : 1240934903,
                               'enabled' : False,
                             },
    'imageDownloads' : { 'uri' : 'imageDownloads',
                         'name' : 'Images Downloaded',
                         'description' : 'Show the number of images downloaded by systems',
                         'timecreated' : 1240934903,
                          'enabled' : False,
                       },
    'applianceDownloads' : { 'uri' : 'applianceDownloads',
                         'name' : 'Downloads for an Appliance',
                         'description' : 'Show the number of images downloaded by Appliance',
                         'timecreated' : 1240934903,
                          'enabled' : False,
                       },
}       