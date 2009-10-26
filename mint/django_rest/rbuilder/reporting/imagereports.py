from mint.django_rest.rbuilder.models import Images, Products
from mint.django_rest.rbuilder.reporting.reports import TimeSegmentReport

from django.db import connection, transaction
from django.db.models import Count
from django.http import HttpResponse
from django_restapi.resource import Resource

from xobj import xobj

from datetime import date
import time
import calendar

class ImagesPerProduct(Resource):
    
    def _getEpoch(self, kwargs):
        year = (('year' in kwargs and kwargs['year']) or 1)
        month = (('month' in kwargs and kwargs['month']) or 1)
        day = (('day' in kwargs and kwargs['day']) or 1)
        
        return (time.mktime(date(year, month, day).timetuple()))
        
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
        
        cursor = connection.cursor()
        
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
        
        cursor.execute(sql_query % locals())
         
        segreport = TimeSegmentReport(request, units, starttime, endtime)
        
        for row in cursor.fetchall():
            total = row[-1]
            time = self._getTimeConversion(units)(self, dict(zip(extracts,row[:-1])))
            segment = segreport.timeSegments.Segment(total, time)
            segreport.addSegment(segment)
        
        return HttpResponse(xobj.toxml(segreport, report), "text/plain")
     
    #    
    _time_units_matrix = {'year': {'extracts' : ['year',],
                                   'timeConv' : _getEpoch,
                                  },
                           'month': {'extracts':['year','month',],
                                   'timeConv' : _getEpoch,
                                  },
                           'day': {'extracts':['year','month','day'],
                                   'timeConv' : _getEpoch,
                                  },
                          }
