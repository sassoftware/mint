from mint.django_rest.rbuilder.reporting import imagereports, rbuilderreports

from django.http import Http404, HttpResponse
from django_restapi.resource import Resource
        
class ReportDispatcher(Resource):
        
    def dispatch(self, request, target, *args, **kwargs):
        #Get the class and an instance of it for the actual report to use
        
        if args[0] not in _reportMatrix:
            raise Http404('Report Type: %s' % args[0])
        if _reportMatrix[args[0]]['admin'] and not request._is_admin:
            response =  HttpResponse('Access denied', mimetype="text/plain")
            response.status_code = 403
            return response

        obj = _reportMatrix[args[0]]['reportClass']
            
        return Resource.dispatch(self, request, obj(), *args, **kwargs)
        
class ReportDescriptor(Resource):

    def read(self, request, report):       
        descriptor = _reportMatrix[report]['descriptor'] % request.build_absolute_uri()
        
        return HttpResponse(descriptor, "text/plain")       

# FIXME:  This is tied to the views.py code          
_reportMatrix = {'imagesReport': 
  { 'reportClass' : imagereports.ImagesPerProduct,
    'admin' : False,
    'descriptor' : """<?xml version="1.0" encoding="UTF-8"?>
<views>
    <view
        id="%s"
        label="Image Creation Timeline"
    >
       <pod id="ipc"
          type="SmartLineChart"
          title="Images per Product"
          rootElement="quarters"
          dataElement="file"
          dateField="report_day"
          dateUnits="days"
          selectedViewIndex="0"
          dataTipUnitLabel="$*"
          dataTipLabelField="Total"
       />
   </view>
</views>"""
  },
  'systemUpdateCheck': 
  { 'reportClass' : rbuilderreports.SystemUpdateCheck,
    'admin' : True,
    'descriptor' : """<?xml version="1.0" encoding="UTF-8"?>
<views>
    <view
        id="%s"
        label="System Updates"
    >
       <pod id="ipc"
          type="SmartLineChart"
          title="System Updates"
          rootElement="quarters"
          dataElement="file"
          dateField="report_day"
          dateUnits="days"
          selectedViewIndex="0"
          dataTipUnitLabel="$*"
          dataTipLabelField="Total"
       />
   </view>
</views>"""
  },
  'imageDownloads': 
  { 'reportClass' : imagereports.ImagesDownloaded,
    'admin' : True,
    'descriptor' : """<?xml version="1.0" encoding="UTF-8"?>
<views>
    <view
        id="%s"
        label="Images Downloaded"
    >
       <pod id="ipc"
          type="SmartLineChart"
          title="System Updates"
          rootElement="quarters"
          dataElement="file"
          dateField="report_day"
          dateUnits="days"
          selectedViewIndex="0"
          dataTipUnitLabel="$*"
          dataTipLabelField="Total"
       />
   </view>
</views>"""
  },
  'applianceDownloads': 
  { 'reportClass' : imagereports.ApplianceDownloads,
    'admin' : False,
    'descriptor' : """<?xml version="1.0" encoding="UTF-8"?>
<views>
    <view
        id="%s"
        label="Appliance Downloads"
    >
       <pod id="ipc"
          type="SmartLineChart"
          title="System Updates"
          rootElement="quarters"
          dataElement="file"
          dateField="report_day"
          dateUnits="days"
          selectedViewIndex="0"
          dataTipUnitLabel="$*"
          dataTipLabelField="Total"
       />
   </view>
</views>"""
  },
}