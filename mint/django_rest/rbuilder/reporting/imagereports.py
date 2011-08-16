from mint.django_rest.rbuilder import reporting
from mint.django_rest.rbuilder.projects.models import Project #, Downloads
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
    
    # Handle GET methods
    def read(self, request, report, product):
        
        # Check what parameters were sent as part of the get
        units = ((request.REQUEST.has_key('timeunits') 
            and request.REQUEST['timeunits']) or 'month')
        starttime = ((request.REQUEST.has_key('starttime') 
            and request.REQUEST['starttime']) or None)
        endtime = ((request.REQUEST.has_key('endtime') 
            and request.REQUEST['endtime']) or None)
        
        if units not in ('year','month','day','hour'):
            return HttpResponseBadRequest('Invalid timeunits value: %s' % units)
        
        # Make sure that the arguments are only numbers
        pattern = re.compile('^(([0-9]+(\.)?[0-9]+)|([0-9]+))$')    
        for param in (starttime, endtime,):
            if param is not None and not pattern.match(param):
                return HttpResponseBadRequest('Invalid query parameter: %s' 
                    % param)       

        qargs = dict(product=product, units=units)       
        where_stmt = " WHERE p.shortname = %(product)s and p.projectid = b.projectid"
        
        if starttime:
            where_stmt += " and b.timecreated > %(starttime)s" % locals()
            qargs['starttime'] = starttime

        if endtime:
            where_stmt += " and b.timecreated < %(endtime)s" % locals()
            qargs['endtime'] = endtime
            
        sql_query = """SELECT date_trunc(%(units)s, timestamp with time zone 'epoch' 
            + cast (b.timecreated as INTEGER) * INTERVAL 
            '1 second'), count(1)
            from builds b, projects p 
            """
            
        sql_query += where_stmt + " group by 1 order by 1"""
        
        cursor = connection.cursor()
        
        cursor.execute(sql_query, qargs )
         
        segreport = TimeSegmentReport(request, units, starttime, endtime)
        
        rows = cursor.fetchall()
        
        #Check to see if any rows were returned and if the cause was due to 
        #nonexistent product
        if not rows:
            try:
                product = Project.objects.get(short_name=product)
            except Project.DoesNotExist, data:
                raise Http404(data)
        
        for row in rows:
            total = row[-1]
            t =  time.mktime(row[0].timetuple())
            segment = segreport.timeSegments.Segment(total, t)
            segreport.addSegment(segment)
        
        return HttpResponse(xobj.toxml(segreport, report), "text/plain")
    
class ImagesDownloaded(Resource):
    
    # Handle GET methods
    def read(self, request, report, product):

        # Check what parameters were sent as part of the get
        units = ((request.REQUEST.has_key('timeunits') 
            and request.REQUEST['timeunits']) or 'month')
        starttime = ((request.REQUEST.has_key('starttime') 
            and request.REQUEST['starttime']) or None)
        endtime = ((request.REQUEST.has_key('endtime') 
            and request.REQUEST['endtime']) or None)
        
        if units not in reporting._time_units_matrix:
            return HttpResponseBadRequest('Invalid timeunits value: %s' % units)
        
        # Make sure that the arguments are only numbers
        pattern = re.compile('^(([0-9]+(\.)?[0-9]+)|([0-9]+))$')    
        for param in (starttime, endtime,):
            if param is not None and not pattern.match(param):
                return HttpResponseBadRequest('Invalid query parameter: %s' 
                        % param)       
               
        rows = Downloads.objects.extra\
            (select={'time':"SUBSTRING(TEXT(timedownloaded),1,%d)" %\
             size[units]['length']}).values('time').distinct().\
             annotate(downloads = Count('ip'))
        
        segreport = TimeSegmentReport(request, units, starttime, endtime)
        for row in rows:
            total = row['downloads']
            t =  time.mktime(time.strptime(row['time'], size[units]['format']))
            segment = segreport.timeSegments.Segment(total, t)
            segreport.addSegment(segment)
        
        return HttpResponse(xobj.toxml(segreport, report), "text/plain")
 
class ApplianceDownloads(Resource):

    # Handle GET methods
    def read(self, request, report, product):
        
        # Check what parameters were sent as part of the get
        units = ((request.REQUEST.has_key('timeunits') 
            and request.REQUEST['timeunits']) or 'month')
        starttime = ((request.REQUEST.has_key('starttime') 
            and request.REQUEST['starttime']) or None)
        endtime = ((request.REQUEST.has_key('endtime') 
            and request.REQUEST['endtime']) or None)
        
        if units not in ('year','month','day','hour'):
            return HttpResponseBadRequest('Invalid timeunits value: %s' % units)
        
        # Make sure that the arguments are only numbers
        pattern = re.compile('^(([0-9]+(\.)?[0-9]+)|([0-9]+))$')    
        for param in (starttime, endtime,):
            if param is not None and not pattern.match(param):
                return HttpResponseBadRequest('Invalid query parameter: %s' 
                        % param)       

        length = size[units]['length']
        
        qargs = dict(product=product, length=length)
        where_stmt = """ WHERE p.projectid=b.projectid and dl.urlid =  bfu.urlid 
            and bf.fileid = bfu.fileid and bf.buildid = b.buildid
            and p.shortname = %(product)s""" 
        
        if starttime:
            startpoint = time.strftime('%Y%m%d%H%M%S', time.localtime(float(starttime)))
            where_stmt += " and timedownloaded > %s" % startpoint
             
        if endtime:
            endpoint = time.strftime('%Y%m%d%H%M%S', time.localtime(float(endtime)))
            where_stmt += " and timedownloaded < %s" % endpoint     
        
#FIXME: This needs to be more djangoized and the table relationships can use another look               
        sql_query = """select DISTINCT (SUBSTRING(TEXT(timedownloaded),1,%(length)s)) AS "time", COUNT(dl."ip") AS "downloads" 
            FROM urldownloads dl, projects p, builds b, buildfilesurlsmap bfu, buildfiles bf
            """ + where_stmt + " GROUP BY 1"
            
        cursor = connection.cursor()
        
        cursor.execute(sql_query, qargs )
        
        segreport = TimeSegmentReport(request, units, starttime, endtime)
        
        rows = cursor.fetchall()

        #Check to see if any rows were returned and if the cause was due to 
        #nonexistent product
        if not rows:
            try:
                product = Project.objects.get(short_name=product)
            except Project.DoesNotExist, data:
                raise Http404(data)
 
        for row in rows:
            total = row[1]
            t =  time.mktime(time.strptime(row[0], size[units]['format']))
            segment = segreport.timeSegments.Segment(total, t)
            segreport.addSegment(segment)
        
        return HttpResponse(xobj.toxml(segreport, report), "text/plain")

size = {'year': {'length':4,'format':'%Y'}, 
                'month': {'length':6, 'format' : '%Y%m'},
                'day' : {'length':8, 'format' : '%Y%m%d'},
                'hour' : {'length':10, 'format' : '%Y%m%d%H'},
               }
