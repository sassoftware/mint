from mint.django_rest import rbuilder

from xobj import xobj

class TimeSegmentReport(object):

    _xobj = xobj.XObjMetadata(
	    attributes = {
		             'id' : str,
				     },
	    elements = ['timeSegments','startTime','endTime','timeUnits',]
	    )

    class TimeSegment(object):
        
        class Segment(object):
            _xobj = xobj.XObjMetadata(
	            attributes = {
		             'id' : str,
				     },
	            )
        
            def __init__(self, total, time, id = None):
                self.total = int(total)
                self.time = int(time)
                if id:
                    self.id = id
        
        def __init__(self):
            self.timeSegment = []
    
    def __init__(self, request, timeUnits, startTime = None, endTime = None):
        self.id = rbuilder.IDElement(request.build_absolute_uri())
        self.startTime = startTime
        self.endTime = endTime
        self.timeUnits = timeUnits
        self.timeSegments = self.TimeSegment()
        
        
    def addSegment(self, segment):
        if len(self.timeSegments.timeSegment) == 0 or segment.time < self.startTime:
            self.startTime = segment.time
        if segment.time > self.endTime:   
            self.endTime = segment.time
        self.timeSegments.timeSegment.append(segment)

        