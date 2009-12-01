#
import time

def _incrementTime(time, units):
    return _time_units_matrix[units]['delta'](time)

def _incrementYear(starttime):
    timetuple = time.localtime(starttime)
    timelist = list(timetuple)
    timelist[0] = timelist[0] + 1
    return time.mktime(tuple(timelist))
    
def _incrementMonth(starttime):
    timetuple = time.localtime(starttime)
    timelist = list(timetuple)
    timelist[8] = -1
    if timelist[1] == 12:
        timelist[0] = timelist[0] + 1
        timelist[1] = 1
    else:
        timelist[1] = timelist[1] + 1 
    return time.mktime(tuple(timelist))           
    
def _incrementDay(starttime):
    incrtime = starttime + 60 * 60 * 24
    timetuple = time.localtime(incrtime)
    #Make sure DST didn't offset the increment
    hours = timetuple[3]
    if hours != 0:
        if hours == 23:
            incrtime += 60 * 60
        elif hours == 1:
            incrtime -= 60 * 60  
    return incrtime 
    
def _incrementHour(starttime):
    return starttime + 60 * 60

# Matrix of time units to the order of time elements to have distinct values
_time_units_matrix = {'year': {'delta' : _incrementYear},
                       'month': {'delta' : _incrementMonth},
                       'day': {'delta' : _incrementDay},
                       'hour': {'delta' : _incrementHour},     
                      }
