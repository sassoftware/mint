#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

import database
import feedparser

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
                );"""
    fields = ['itemId', 'title', 'pubDate', 'content', 'link', 'category']

    def __init__(self, db, cfg):
        database.DatabaseTable.__init__(self, db)
        self.cfg = cfg

    def refresh(self, items = 5, purge = True):
        if not self.cfg.newsRssFeed:
            return

        cu = self.db.cursor()

        if purge:
            cu.execute("DELETE FROM NewsCache")

        fp = feedparser.parse(self.cfg.newsRssFeed)

        for item in fp['items'][:5]:
            query = "INSERT INTO NewsCache VALUES (NULL, ?, ?, ?, ?, ?)"
            cu.execute(query, item['title'], 0, item['content'][0]['value'][:60],
                              item['link'], item['category'])
        self.db.commit()

    def getNews(self):
        cu = self.db.cursor()

        cu.execute("SELECT * FROM NewsCache ORDER BY pubDate")
        data = []

        for r in cu.fetchall():
            item = {}
            for i, key in enumerate(self.fields):
                item[key] = r[i]
            data.append(item)
        return data
                                            
