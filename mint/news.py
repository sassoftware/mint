#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

import calendar
import time
import rfc822
import urllib2 
from elementtree import ElementTree

import database

REFRESH_TIME = 600 # seconds

class NewsCacheAgeTable(database.DatabaseTable):
    name = 'NewsCacheAge'
    fields = ['age']

    createSQL = "CREATE TABLE NewsCacheAge (age INT);"

    def getAge(self):
        cu = self.db.cursor()
        cu.execute("SELECT age FROM NewsCacheAge")
        
        r = cu.fetchone()
        if r:
            age = r[0]
        else:
            age = 0
        return age

    def setAge(self):
        cu = self.db.cursor()
        cu.execute("DELETE FROM NewsCacheAge")
        cu.execute("INSERT INTO NewsCacheAge VALUES (?)", time.time())
        self.db.commit()
        return True
        
class NewsCacheTable(database.KeyedTable):
    name = 'NewsCache'
    key = 'itemId'
    createSQL = """CREATE TABLE NewsCache (
                    itemId          INTEGER PRIMARY KEY,
                    title           STR,
                    pubDate         INT,
                    content         STR,
                    link            STR,
                    category        STR
                );
                """
    fields = ['itemId', 'title', 'pubDate', 'content', 'link', 'category']

    def __init__(self, db, cfg):
        database.DatabaseTable.__init__(self, db)
        self.cfg = cfg
        self.ageTable = NewsCacheAgeTable(db)

    def refresh(self, items = 5, purge = True):
        def toUnixTime(t):
            return calendar.timegm(rfc822.parsedate_tz(item.find("pubDate").text))
    
        if not self.cfg.newsRssFeed:
            return False

        if (time.time() - REFRESH_TIME) < self.ageTable.getAge():
            return False

        cu = self.db.cursor()

        if purge:
            cu.execute("DELETE FROM NewsCache")

        url = urllib2.urlopen(self.cfg.newsRssFeed)
        data = url.read()

        tree = ElementTree.XML(data)
        for item in tree.findall("channel/item")[:items]:
            link = item.find("link").text
            title = item.find("title").text
            category = item.find("category").text
            pubDate = toUnixTime(item.find("pubDate").text)
        
            query = "INSERT INTO NewsCache VALUES (NULL, ?, ?, ?, ?, ?)"
            cu.execute(query, title, pubDate, '', link, category)
        
        self.ageTable.setAge()
        self.db.commit()
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
