from mint.django_rest.rbuilder.reporting.models import SystemUpdate
from mint.django_rest.rbuilder.reporting.reports import TimeSegmentReport

from django.db import connection, transaction
from django.db.models import Count
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django_restapi.resource import Resource

from xobj import xobj

from datetime import datetime
import time
import calendar
import re

class SystemUpdateCheck(Resource):
    
    def _getEpoch(self, kwargs):
        year = int((('year' in kwargs and kwargs['year']) or 1))
        month = int((('month' in kwargs and kwargs['month']) or 1))
        day = int((('day' in kwargs and kwargs['day']) or 1))
        hour = int((('hour' in kwargs and kwargs['hour']) or 0))
        
        return (time.mktime(datetime(year, month, day, hour).timetuple()))
        
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
        
    def _getTimeDelta(self, timeUnit):
        return self._time_units_matrix[timeUnit]['delta']
        
    def _getResource(self, request, report, resource):
        units = ((request.REQUEST.has_key('timeunits') and 
            request.REQUEST['timeunits']) or 'month')

        delta = self._getTimeDelta(units)
        start = int(resource)
        end = delta(self,start)
        
        sql_query = """select servername, repositoryName, count(1)
            from systemupdate s
            where s.updatetime between %(start)d and %(end)d
            group by servername, repositoryName
            order by servername"""
        cursor = connection.cursor()

        cursor.execute(sql_query % locals())
        
        segreport = TimeSegmentReport(request, units, start, end)
        
        rows = cursor.fetchall()
        
        for row in rows:
            #import epdb;epdb.st()
            total = row[2]          
            time = resource
            id = request.build_absolute_uri(str(int(time)) + '?timeunits=' + units)
            segment = segreport.timeSegments.Segment(total, time)
            segment.systems = row[0]
            segment.repository = row[1]
            segreport.addSegment(segment)
            
        return HttpResponse(xobj.toxml(segreport, report), "text/plain")
       
    
    # Handle GET methods
    def read(self, request, report, resource):
    
        if resource:
            return self._getResource(request, report, resource)
       
        # Check what parameters were sent as part of the get
        units = ((request.REQUEST.has_key('timeunits') and 
            request.REQUEST['timeunits']) or 'month')
        starttime = ((request.REQUEST.has_key('starttime') and 
            request.REQUEST['starttime']) or None)
        endtime = ((request.REQUEST.has_key('endtime') and 
            request.REQUEST['endtime']) or None)
        
        if units not in self._time_units_matrix:
            return HttpResponseBadRequest('Invalid timeunits value: %s' % units)
        
        # Make sure that the arguments are only numbers
        pattern = re.compile('^(([0-9]+(\.)?[0-9]+)|([0-9]+))$')    
        for param in (starttime, endtime,):
            if param is not None and not pattern.match(param):
                     return HttpResponseBadRequest('Invalid query parameter: %s' % param)       
               
        extract_stmt = """date_trunc('%s', timestamp with time zone 'epoch' 
             + cast (s.updatetime as INTEGER) * INTERVAL 
             '1 second')""" % units

        where_stmt = ""
        
        if starttime:
            where_stmt += " and b.timecreated > %(starttime)s" % locals()
            
        if endtime:
            where_stmt += " and b.timecreated < %(endtime)s" % locals()
                
        sql_query = """SELECT %(extract_stmt)s, count(distinct(servername)), count(1)
            from systemupdate s
            %(where_stmt)s 
            group by %(extract_stmt)s
			order by %(extract_stmt)s"""
        
        cursor = connection.cursor()
        #print sql_query % locals()
        cursor.execute(sql_query % locals())
         
        segreport = TimeSegmentReport(request, units, starttime, endtime)
        
        rows = cursor.fetchall()
        
        for row in rows:
            #import epdb;epdb.st()
            total = row[-1]          
            print row[0].timetuple()
            t = time.mktime(row[0].timetuple())
            id = request.build_absolute_uri(str(int(t)) + '?timeunits=' + units)
            segment = segreport.timeSegments.Segment(total, t, id)
            segment.systems = row[-2]
            segreport.addSegment(segment)
        
        return HttpResponse(xobj.toxml(segreport, report), "text/plain")
     
    # Matrix of time units to the order of time elements to have distinct values
    _time_units_matrix = {'year': {'delta' : _incrementYear},
                           'month': {'delta' : _incrementMonth},
                           'day': {'delta' : _incrementDay},
                           'hour': {'delta' : _incrementHour},     
                          }
