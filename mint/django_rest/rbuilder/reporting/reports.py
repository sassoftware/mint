from mint.django_rest import rbuilder

from xobj import xobj

import time

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
            
        if self.timeSegments.timeSegment:
            self._fillInBlanks(self.timeSegments.timeSegment[-1], segment)    
        self.timeSegments.timeSegment.append(segment)
        
    def _fillInBlanks(self, segment, nextSegment):
        timeindex = self._incrementTime(segment.time, self.timeUnits)
        while timeindex < nextSegment.time:	        
	        zeroSeg = self.TimeSegment.Segment(0, timeindex)
	        self.timeSegments.timeSegment.append(zeroSeg)
	        timeindex =  self._incrementTime(timeindex, self.timeUnits)
    
    def _incrementTime(self, time, units):
        return self._time_units_matrix[units]['delta'](self,time)
    
    def _incrementYear(self, starttime):
        timetuple = time.localtime(starttime)
        timelist = list(timetuple)
        timelist[0] = timelist[0] + 1
        return time.mktime(tuple(timelist))
        
    def _incrementMonth(self, starttime):
        timetuple = time.localtime(starttime)
        timelist = list(timetuple)
        if timelist[1] == 12:
            timelist[0] = timelist[0] + 1
            timelist[1] = 1
        else:
            timelist[1] = timelist[1] + 1 
        return time.mktime(tuple(timelist))           
        
    def _incrementDay(self, starttime):
        return starttime + 60 * 60 * 24
        
    def _incrementHour(self, starttime):
        return starttime + 60 * 60

    # Matrix of time units to the order of time elements to have distinct values
    _time_units_matrix = {'year': {'delta' : _incrementYear},
                           'month': {'delta' : _incrementMonth},
                           'day': {'delta' : _incrementDay},
                           'hour': {'delta' : _incrementHour},     
                          }
        