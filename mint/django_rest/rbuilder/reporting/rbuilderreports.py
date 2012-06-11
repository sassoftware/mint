from mint.django_rest.rbuilder import reporting
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
       
    def _getResource(self, request, report, resource):
        units = ((request.REQUEST.has_key('timeunits') and 
            request.REQUEST['timeunits']) or 'month')

        start = int(resource)
        end = reporting._incrementTime(start, units)
        
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
        
        if units not in reporting._time_units_matrix:
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
            where_stmt += " and s.updatetime > %(starttime)s" % locals()
            
        if endtime:
            where_stmt += " and s.updatetime < %(endtime)s" % locals()
                
        sql_query = """SELECT %(extract_stmt)s, count(distinct(servername)), count(1)
            from systemupdate s
            %(where_stmt)s 
            group by %(extract_stmt)s
			order by %(extract_stmt)s"""
        
        cursor = connection.cursor()
        
        cursor.execute(sql_query % locals())
         
        segreport = TimeSegmentReport(request, units, starttime, endtime)
        
        rows = cursor.fetchall()
        
        for row in rows:
            total = row[-1]          
            t = time.mktime(row[0].timetuple())
            id = request.build_absolute_uri(str(int(t)) + '?timeunits=' + units)
            segment = segreport.timeSegments.Segment(total, t, id)
            segment.systems = row[-2]
            segreport.addSegment(segment)
        
        return HttpResponse(xobj.toxml(segreport, report), "text/plain")

