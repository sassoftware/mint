#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import string
import re
import time

NEVER, DAY, THREEDAYS, WEEK, TWOWEEKS, FOURWEEKS = range(0, 6)

datehtml = [
    "Any Time",
    "24 Hours",
    "3 Days",
    "7 Days",
    "2 Weeks",
    "4 Weeks",
]

datesql = {
    NEVER: "0",
    DAY: "(EPOCH - 86400)",
    THREEDAYS: "(EPOCH - 259200)",
    WEEK: "(EPOCH - 604800)",
    TWOWEEKS: "(EPOCH - 1209600)",
    FOURWEEKS: "(EPOCH - 2419200)",
}

class Searcher :
    WORDS_PRE = 30
    WORDS_POST = 30
    WORDS_TOTAL = 60

    @classmethod
    def lastModified(self, column, modcode):
        if modcode == NEVER:
            return ''
        else:
            comparator = datesql[modcode].replace('EPOCH', str(time.time()))
            return "%s > %s" % (column, comparator)

    @classmethod
    def truncate(self, longstring, searchterms):
        """
        Shortens L{longstring} around L{searchterms} so that a long string can
        be easily displayed in a search results page.
        To change the number of words to truncate to, create an instance of this
        class and change the values of L{WORDS_PRE}, L{WORDS_POST} and/or L{WORDS_TOTAL}.
        @param longstring:  The original string
        @param searchterms: Search terms to find within the string
        @return:       a dictionary of the requested items.
                       each entry will contain four bits of data:
                        The hostname for use with linking,
                        The project name,
                        The project's description
                        The date last modified.

        """
        #are the search terms in the string
        returner = longstring
        if returner == None:
            return ''
        if searchterms in longstring:
            #Split it up and shorten it
            regexp = "(\S+\s+){0,%d}" % self.WORDS_PRE + searchterms + "(\s+\S+){0,%d}" % self.WORDS_POST
            expr = re.compile(regexp, re.IGNORECASE)
            match = expr.search(longstring)
            if match != None:
                returner = match.group().strip()
            if longstring != returner:
                if longstring.find(returner) == 0:
                    returner += '...'
                else:
                    returner = '...' + returner + '...'
        else:
            #simply truncate it
            shortened = re.match('^(\S+\s+){0,%d}' % self.WORDS_TOTAL, longstring).group().strip()
            if longstring != shortened:
                shortened += '...'
            returner = shortened
        return returner


    @classmethod
    def where(self, searchterms, searchcols):
        """
        Creates a WHERE clause based on L{searchterms}.
        XXX: Need to add sophistication
        @param searchterms: the terms on which to search
        @param searchcols:  the columns to search for searchterms
        @return:        A string containing the where clause for the given L{searchterms}
        """
        where = " WHERE "
        for i, column in enumerate(searchcols):
            if i > 0:
                where += "OR "
            where += "%(a)s LIKE '%%%(b)s%%' " % {'a' : column, 'b' : searchterms}

        return where
