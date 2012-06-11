from mint.django_rest.rbuilder import auth
from mint.django_rest.rbuilder.xobj_responder import xobjResponder
from mint.django_rest.rbuilder.reporting.models import Report, Reports

from xobj import xobj

from django.http import HttpResponse, Http404
from django_restapi.resource import Resource

class ReportView(Resource):

    # Handle GET methods
    def read(self, request, reportName=None):

        if reportName:
            if reportName not in _reports:
                raise Http404
                
            report = Report()
            for attr in _reports[reportName].items():              
                setattr(report, attr[0], attr[1])
                
            report.populateElements(request)
            return HttpResponse(xobj.toxml(report, 'report'), "text/plain")
        else:
	        queryset = []
	        for type in _reports.values():
	            report = Report()
	            for attr in type.items():              
	                setattr(report, attr[0], attr[1])
	            
	            report.populateElements(request)    
	            queryset.append(report)
	        
	        obj = Reports()
	        obj.addQueryset(queryset)
	        return HttpResponse(xobj.toxml(obj, obj.__class__.__name__), "text/plain")     

# FIXME:  This is tied to the reportdispatcher.py code        
_reports = {
    'imagesReport': { 'uri' : 'imagesReport',
                      'name' : 'Image Creation Timeline',
                      'description': 'Show the number of images created for a product by different aggregations',
                      'timecreated': 1240934903,
                      'adminReport' : False,
                    },
    'systemUpdateCheck' : { 'uri' : 'systemUpdateCheck',
                            'name' : 'System Update Check',
                            'description' : 'Show the number of systems checking for updates from this rBuilder Appliance',
                            'timecreated' : 1240934903,
                            'adminReport' : True,
                             },
    'imageDownloads' : { 'uri' : 'imageDownloads',
                         'name' : 'Images Downloaded',
                         'description' : 'Show the number of images downloaded by systems',
                         'timecreated' : 1240934903,
                         'adminReport' : True,
                       },
    'applianceDownloads' : { 'uri' : 'applianceDownloads',
                         'name' : 'Downloads for an Appliance',
                         'description' : 'Show the number of images downloaded by Appliance',
                         'timecreated' : 1240934903,
                         'adminReport' : False,
                       },
}       