from mint.django_rest.rbuilder.models import Images, Products

from django.db import connection, transaction
from django.db.models import Count
from django.http import HttpResponse, QueryDict
from django_restapi.resource import Resource

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
    
    def read(self, request, product):
        allowed_params = ['starttime','endtime','timeunits']
        allowed_time_units = ['month']
        
        # Default the units to months if none is sent
        units = 'month'
        
        # Get the query string parameters
        queryparams = QueryDict(request.META['QUERY_STRING'].lower())
        
        if 'timeunits' in queryparams:
        	units = queryparams['timeunits']
        
        cursor = connection.cursor()
        
        extracts = self._getCalendarComponents(units)
        
        extract_stmt = ""
        extract_len = len(extracts)
        
        for extract in extracts:
            extract_stmt += " extract (%s from timestamp with time zone 'epoch' + cast (b.timecreated as INTEGER) * INTERVAL '1 second') "	% extract
            if (extracts.index(extract) != extract_len - 1):
                extract_stmt += ","
                
        sql_query = """SELECT %(extract_stmt)s, count(1)
            from builds b, projects p 
            where p.shortname = '%(product)s' and p.projectid = b.projectid 
            group by %(extract_stmt)s
			order by %(extract_stmt)s"""
        
        cursor.execute(sql_query % vars())
         
        vals = "<?xml version='1.0' encoding='UTF-8'?>\n<imagesPerProduct id=\"http://%s%s\">\n    <timeSegments>\n" % (request.get_host(),request.path)
        
        for row in cursor.fetchall():
            vals +="        <timeSegment>\n"
            vals += "           <total>%i</total>\n" % row[-1] 
            vals += "           <time>%i</time>\n" % self._getTimeConversion(units)(self, dict(zip(extracts,row[:-1])))
            vals +="        </timeSegment>\n"
        
        vals += "    </timeSegments>\n    <timeUnits>%s</timeUnits>\n</imagesPerProduct>" % units
        return HttpResponse(unicode(vals), "text/plain")
     
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
