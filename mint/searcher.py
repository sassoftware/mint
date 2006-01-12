#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import string
import re
import time
from mint_error import MintError

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
    MINLENGTH = 3

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
    def where(self, searchterms, searchcols, extras=''):
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
        for orchunk in orsplit.split(terms):
            orchunk = orchunk.strip()
            if orchunk:
                andtoks = []
                andsubs = []
                # Split on double quotes.  Odd numbered splits get columnified
                # so long as they meet length requirements
                # Even numbered splits get further treatment
                for j, quotechunk in enumerate(orchunk.split('"')):
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
                ortoks.append( ' AND '.join(andtoks) )
                substitutions.extend(andsubs)

        # Finally paste the OR blocks together
        where += ' OR '.join(ortoks)

        # If nothing results, raise SearchTermsError
        if not where.strip():
            raise SearchTermsError

        return "WHERE " + where + " " + extras, substitutions

    @classmethod
    def tokenize(self, searchterms, searchcols):
        tokens = []
        substitutions = []
        for term in searchterms.split():
            if len(term) >= self.MINLENGTH:
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
            where += "%s LIKE ? " % column
            subs.append ( '%' + term + '%' )
        where += ') '
        return where, subs

