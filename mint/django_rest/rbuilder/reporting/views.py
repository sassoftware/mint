from django_restapi.model_resource import Collection
from django_restapi.responder import XMLResponder

from rbuilder.reporting.models import ReportType

class ReportTypeCollection(Collection):
    pass
    
def reportTypeCollection():
    return ReportTypeCollection(
        queryset = ReportType.objects.all(),
        permitted_methods = ('GET',),
        responder = XMLResponder(),
    )
