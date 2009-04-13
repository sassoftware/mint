#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

import calendar
from elementtree import ElementTree
import socket
import sys
import time
import rfc822
import urllib2

from mint import logerror
from mint.lib import database

REFRESH_TIME = 600 # seconds

class NewsCacheInfoTable(database.DatabaseTable):
    name = 'NewsCacheInfo'
    fields = ['age', 'feedLink']

    def getAge(self):
        cu = self.db.cursor()
        cu.execute("SELECT age FROM NewsCacheInfo")
        
        r = cu.fetchone()
        return r and r[0] or 0

    def getLink(self):
        cu = self.db.cursor()
        cu.execute("SELECT feedLink FROM NewsCacheInfo")

        r = cu.fetchone()
        return r and r[0] or ""
        
    def set(self, t, link):
        cu = self.db.cursor()
        cu.execute("DELETE FROM NewsCacheInfo")
        cu.execute("INSERT INTO NewsCacheInfo VALUES (?, ?)", t, link)
        self.db.commit()
        return True
        
class NewsCacheTable(database.KeyedTable):
    name = 'NewsCache'
    key = 'itemId'

    fields = ['itemId', 'title', 'pubDate', 'content', 'link', 'category']

    def __init__(self, db, cfg):
        database.DatabaseTable.__init__(self, db)
        self.cfg = cfg
        self.ageTable = NewsCacheInfoTable(db)

    def refresh(self, items = 5, purge = True):
        def toUnixTime(t):
            return calendar.timegm(rfc822.parsedate_tz(item.find("pubDate").text))

        if not self.cfg.newsRssFeed:
            return False

        if (time.time() - REFRESH_TIME) < self.ageTable.getAge():
            return False

        timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(3)
        try:
            try:
                url = urllib2.urlopen(self.cfg.newsRssFeed)
                data = url.read()
            except (urllib2.URLError, socket.error):
                e_type, e_value, e_tb = sys.exc_info()
                logerror.logErrorAndEmail(self.cfg, e_type, e_value, e_tb,
                        'RSS feed reader', dict(url=self.cfg.newsRssFeed),
                        doEmail=False)
                return False
        finally:
            socket.setdefaulttimeout(timeout)

        if purge:
            cu = self.db.cursor()
            cu.execute("DELETE FROM NewsCache")
            self.db.commit()

        try:
            cu = self.db.transaction()
            tree = ElementTree.XML(data)
            feedLink = tree.find("channel/link").text
            for item in tree.findall("channel/item")[:items]:
                link = item.find("link").text
                title = item.find("title").text
                category = item.find("category").text
                content = item.find("{http://purl.org/rss/1.0/modules/content/}encoded").text
                pubDate = toUnixTime(item.find("pubDate").text)
            
                cu.execute("""INSERT INTO NewsCache (
                        title, pubDate, content, link, category )
                            VALUES (?, ?, ?, ?, ?)""",
                        title, pubDate, content, link, category)
        except:
            e_type, e_value, e_tb = sys.exc_info()
            logerror.logErrorAndEmail(self.cfg, e_type, e_value, e_tb,
                    'RSS feed reader', {}, doEmail=False)
            self.db.rollback()
            return False
        else:
            self.db.commit()
            
        self.ageTable.set(t = time.time(), link = feedLink)
        return True

    def getNews(self):
        cu = self.db.cursor()

        cu.execute("SELECT * FROM NewsCache ORDER BY pubDate DESC")
        data = []

        for r in cu.fetchall():
            item = {}
            for i, key in enumerate(self.fields):
                item[key] = r[i]
            data.append(item)
        return data

    def getNewsLink(self):
        return self.ageTable.getLink()
