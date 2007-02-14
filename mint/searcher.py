#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

import re
import string
import time

from mint.mint_error import MintError

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

class SearchError(MintError):
    def __str__(self):
        return "An error has occurred during your search: "

class SearchTermsError(SearchError):
    def __str__(self):
        return SearchError.__str__(self) + "Invalid search terms"


class Searcher :
    WORDS_PRE = 10
    WORDS_POST = 10
    WORDS_TOTAL = 20
    MINLENGTH = 1

    @classmethod
    def lastModified(self, column, modcode):
        if modcode == NEVER:
            return ''
        else:
            comparator = datesql.get(modcode, '0').replace('EPOCH', str(time.time()))
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
        @return:       the shortened string
        """
        returner = longstring
        if returner == None:
            return ''
        #are the search terms in the string
        if searchterms.lower() in longstring.lower():
            #Split it up and shorten it
            regexp = "(\S+\s+){0,%d}\S*" % self.WORDS_PRE + searchterms + "\S*(\s+\S+){0,%d}" % self.WORDS_POST
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
            shortened = re.match('^(\S+\s*){0,%d}' % self.WORDS_TOTAL, longstring).group().strip()
            if longstring != shortened:
                shortened += '...'
            returner = shortened
        return returner


    @classmethod
    def where(self, searchterms, searchcols, extras='', extraSubs = []):
        """
        Creates a WHERE clause based on L{searchterms}.
        XXX: Need to add sophistication
        @param searchterms: the terms on which to search
        @param searchcols:  the columns to search for searchterms
        @return:        A string containing the where clause for the given L{searchterms}
        """
        # find all AND keywords and remove them.  They are redundant
        terms = re.sub('^AND\s+|\s+AND\s+|\s+AND$', ' ', searchterms).strip()

        where = ""
        ortoks = []
        substitutions = []
        # Now split the string on all the OR keywords
        # This method will behave unexpectedly if you have OR within a set i
        # of double quotes.  Caveat searcher.
        orsplit = re.compile('^OR\s+|\s+OR\s+|\s+OR$')

        # pre-filter search terms that are too small to prevent mangled SQL
        for orchunk in [x.strip() for x in orsplit.split(terms) \
                        if len(x.strip()) >= self.MINLENGTH]:
            if orchunk:
                andtoks = []
                andsubs = []
                # Split on double quotes.  Odd numbered splits get columnified
                # so long as they meet length requirements
                # Even numbered splits get further treatment
                for j, quotechunk in \
                    enumerate([x for x in orchunk.split('"') if \
                               len(x) >= self.MINLENGTH]):
                    if j%2:
                        if len(quotechunk) >= self.MINLENGTH:
                            toks, subs = self.columnify(quotechunk, searchcols)
                            andtoks.append(toks)
                            andsubs.extend(subs)
                    else:
                        toks, subs = self.tokenize(quotechunk, searchcols)
                        andtoks.extend(toks)
                        andsubs.extend(subs)
                # now paste the items between the ORs together
                ortoks.append(' AND '.join(andtoks))
                substitutions.extend(andsubs)

        # Finally paste the OR blocks together
        where += ' OR '.join([x for x in ortoks if x])

        # hack
        if not where.strip():
            where = "1"

        return "WHERE " + where + " " + extras, substitutions + extraSubs

    @classmethod
    def tokenize(self, searchterms, searchcols):
        tokens = []
        substitutions = []

        for term in [x for x in searchterms.split()
                     if len(x) >= self.MINLENGTH]:
            toks, subs = self.columnify(term, searchcols)
            tokens.append(toks)
            substitutions.extend(subs)
        return tokens, substitutions

    @classmethod
    def columnify(self, term, searchcols):
        where = '('
        subs = []

        for i, column in enumerate(searchcols):
            if i > 0:
                where += "OR "
            where += "UPPER(%s) LIKE UPPER(?) " % column
            subs.append ( '%' + term + '%' )
        where += ') '
        return where, subs

    @classmethod
    def order(self, terms, searchcols, extra = ''):
        """build SQL for exact match ordering."""
        # throw away *any* search term that is not completely alpha-numeric
        # to prevent sql injection
        tokens = [x for x in terms.split() \
                  if x.upper() not in ('OR', 'AND') and x.isalnum()]
        tokenStr = ', '.join(["UPPER(%s)<>'%s'" % (x, y.upper()) \
                              for x in sorted(searchcols) \
                              for y in sorted(tokens)])
        if tokenStr and extra:
            return ', '.join((tokenStr, extra))
        elif tokenStr:
            return tokenStr
        else:
            return extra


def parseTerms(termsStr):
    """Extract actual search terms and 'limiters' from a string.

       Limiters look like: key=val
    """
    # split and strip
    terms = [x.strip() for x in termsStr.split(" ")]

    # limiters are terms that look like: limiter=key, eg, branch=rpl:1
    limiters = [x for x in terms if '=' in x]
    terms = [x for x in terms if '=' not in x]

    return terms, limiters


def limitersToSQL(limiters, termMap):
    """Convert a set of limiters (key=val) into a SQL string suitable
       for appending to a WHERE clause.
    """
    sql = ""
    subs = []

    for limiter in limiters:
        term, key = limiter.split('=')
        if term not in termMap:
            continue
        sql += " AND %s=?" % (termMap[term])
        subs.append(key)

    return sql, subs

def parseLimiters(termsStr):
    """Return a list of all limiters as 2-tuples (key, value)."""

    limiterlist = []
    terms, limiters = parseTerms(termsStr)
    for limiter in limiters:
        k, v = limiter.split("=")
        if not k or not v:
            continue
        limiterlist.append((k, v),)

    return limiterlist

def limitersForDisplay(termsStr, describeFn = lambda x, y: "%s is %s" % (x, y)):
    """Parse a terms string and return a list of dicts containing
       a 'friendly' description of the limiter, and an associated
       search term string without that limiter, suitable for use
       in a "remove" link.
    """
    limiterInfo = []
    terms, limiters = parseTerms(termsStr)
    for limiter in limiters:
        k, v = limiter.split("=")
        if not k or not v:
            continue

        info = {}
        info['desc'] = describeFn(k, v)
        info['newSearch'] = " ".join((set(limiters) - set([limiter])) | set(terms))
        limiterInfo.append(info)

    return limiterInfo, terms

