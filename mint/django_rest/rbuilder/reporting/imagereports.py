from mint.django_rest.rbuilder.models import Images, Products
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

class ImagesPerProduct(Resource):
    
    def _getEpoch(self, kwargs):
        year = int((('year' in kwargs and kwargs['year']) or 1))
        month = int((('month' in kwargs and kwargs['month']) or 1))
        day = int((('day' in kwargs and kwargs['day']) or 1))
        hour = int((('hour' in kwargs and kwargs['hour']) or 0))
        
        return (time.mktime(datetime(year, month, day, hour).timetuple()))
        
    def _getDayName(self, index):
        return (calendar.day_name[index])
    
    def _getTimeConversion(self, timeUnit):
        return self._time_units_matrix[timeUnit]['timeConv']
        
    def _getCalendarComponents(self, timeUnit):
        return self._time_units_matrix[timeUnit]['extracts']
    
    # Handle GET methods
    def read(self, request, report, product):
        
        # Check what parameters were sent as part of the get
        units = ((request.REQUEST.has_key('timeunits') and request.REQUEST['timeunits']) or 'month')
        starttime = ((request.REQUEST.has_key('starttime') and request.REQUEST['starttime']) or None)
        endtime = ((request.REQUEST.has_key('endtime') and request.REQUEST['endtime']) or None)
        
        if units not in self._time_units_matrix:
            return HttpResponseBadRequest('Invalid timeunits value: %s' % units)
        
        # Make sure that the arguments are only numbers
        pattern = re.compile('^(([0-9]+(\.)?[0-9]+)|([0-9]+))$')    
        for param in (starttime, endtime,):
            if param is not None and not pattern.match(param):
                     return HttpResponseBadRequest('Invalid query parameter: %s' % param)       
        
        extracts = self._getCalendarComponents(units)
        
        extract_stmt = ""
        extract_len = len(extracts)
        
        where_stmt = "p.shortname = '%(product)s' and p.projectid = b.projectid" % locals()
        
        if starttime:
            where_stmt += " and b.timecreated > %(starttime)s" % locals()
            
        if endtime:
            where_stmt += " and b.timecreated < %(endtime)s" % locals()
            
        for extract in extracts:
            extract_stmt += " extract (%s from timestamp with time zone 'epoch' + cast (b.timecreated as INTEGER) * INTERVAL '1 second') "	% extract
            if (extracts.index(extract) != extract_len - 1):
                extract_stmt += ","
                
        sql_query = """SELECT %(extract_stmt)s, count(1)
            from builds b, projects p 
            where %(where_stmt)s 
            group by %(extract_stmt)s
			order by %(extract_stmt)s"""
        
        cursor = connection.cursor()
        
        cursor.execute(sql_query % locals())
         
        segreport = TimeSegmentReport(request, units, starttime, endtime)
        
        rows = cursor.fetchall()
        
        #Check to see if any rows were returned and if the cause was due to 
        #nonexistent product
        if not rows:
            try:
                product = Products.objects.get(shortname=product)
            except Products.DoesNotExist, data:
                raise Http404(data)
        
        for row in rows:
            total = row[-1]
            time = self._getTimeConversion(units)(self, dict(zip(extracts,row[:-1])))
            segment = segreport.timeSegments.Segment(total, time)
            segreport.addSegment(segment)
        
        return HttpResponse(xobj.toxml(segreport, report), "text/plain")
     
    # Matrix of time units to the order of time elements to have distinct values
    _time_units_matrix = {'year': {'extracts' : ['year',],
                                   'timeConv' : _getEpoch,
                                  },
                           'month': {'extracts':['year','month',],
                                   'timeConv' : _getEpoch,
                                  },
                           'day': {'extracts':['year','month','day'],
                                   'timeConv' : _getEpoch,
                                  },
                           'hour': {'extracts':['year','month','day', 'hour'],
                                   'timeConv' : _getEpoch,
                                  },     
                          }
