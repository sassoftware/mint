import time

from conary.repository import shimclient

from mint.rest import modellib
from mint.rest.modellib import fields

class TimingDataField(fields.Field):
    default = 0.0
    def valueToString(self, value, parent, context):
        if value:
            return '%0.4f seconds (%d/second)' % (value, 1.0/value)
        return 'No time'

class SqlQuery(modellib.Model):
    time = TimingDataField(isAttribute=True)
    query = fields.CharField(isText=True)

class ProfileData(modellib.Model):
    responseTime   = TimingDataField()
    sqlTime        = TimingDataField()
    numQueries     = fields.IntegerField()
    sqlQueries     = fields.ListField(SqlQuery)
    repositoryTime = TimingDataField()
    convertTime    = TimingDataField()

    def __init__(self, *args, **kw):
        modellib.Model.__init__(self, *args, **kw)
        self._startResponse = None
        self._startSql = None
        self._startRepos = None
        self.numQueries = 0

    def startResponse(self):
        self._startResponse = time.time()

    def stopResponse(self):
        self.responseTime += time.time() - self._startResponse

    def startSql(self, query):
        self._startSql = (time.time(), query)

    def stopSql(self):
        startTime, sql = self._startSql
        self.numQueries += 1 
        sqlTime = time.time() - startTime
        self.sqlTime += sqlTime
        self.sqlQueries.append(SqlQuery(sqlTime, sql))

    def startRepos(self):
        self._startRepos = time.time()
    
    def stopRepos(self):
        reposTime = time.time() - self._startRepos
        self.repositoryTime += reposTime

    def attachDb(self, db):
        if not hasattr(db, 'oldCursor'):
            db.oldCursor = db.cursor
        def cursor(*args, **kw):
            return CursorWrapper(self, db.oldCursor(*args, **kw))
        db.cursor = cursor

    def attachRepos(self, reposMgr):
        reposMgr.setProfiler(self)

    def wrapRepository(self, repos):
        repos.c = ServerCacheWrapper(self, repos.c)
        return repos

class CursorWrapper(object):
    def __init__(self, profiler, cursor):
        self.__profiler = profiler
        self.__cursor = cursor
        self.execute = self._wrapFn(cursor.execute)
        self.executemany = self._wrapFn(cursor.executemany)

    def _wrapFn(self, fn):
        def wrapper(sql, *args, **kw):
            self.__profiler.startSql(sql)
            results = fn(sql, *args, **kw)
            self.__profiler.stopSql()
            return results
        return wrapper

    def __getattr__(self, key):
        return getattr(self.__cursor, key)

    def __iter__(self):
        return iter(self.__cursor)

class ServerCacheWrapper(object):
    
    def __init__(self, profiler, cache):
        self.__profiler = profiler
        self.__cache = cache

    def __getitem__(self, key):
        return MethodWrapper(self.__profiler, self.__cache[key],
                             self.__profiler.startRepos,
                             self.__profiler.stopRepos)

  
class MethodWrapper(shimclient.ShimServerProxy):
    def __init__(self, profiler, proxy, startFn, stopFn):
        self.__profiler = profiler
        self.__proxy = proxy
        self._startFn = startFn
        self._stopFn = stopFn

    def __getattr__(self, key):
        method = getattr(self.__proxy, key)
        if hasattr(method, '__call__'):
            return self._wrapFn(method)
        return method

    def _wrapFn(slf, fn):
        class Wrapper(object):

            def __call__(self, *args, **kw):
                slf._startFn()
                results = fn(*args, **kw)
                slf._stopFn()
                return results
        return Wrapper()
