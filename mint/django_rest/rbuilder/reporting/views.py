from mint.django_rest.rbuilder.xobj_responder import xobjResponder
from mint.django_rest.rbuilder.reporting.models import ReportType, ReportTypes

from django_restapi.model_resource import Collection

class ReportTypeCollection(Collection):
    pass
    
def reportTypeCollection():
    return ReportTypeCollection(
        queryset = ReportType.objects.all(),
        permitted_methods = ('GET',),
        responder = xobjResponder(model_list = ReportTypes()),
    )
