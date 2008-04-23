#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#

from conary import versions
from conary.deps import deps
from mint import constants
from mint.config import isRBO
from conary.repository.errors import RoleAlreadyExists

import htmlentitydefs
import re
import random
import string
import time
import urlparse

def truncateForDisplay(s, maxWords=10, maxWordLen=15):
    """Truncates a string s for display. May limit the number of words in the
    displayed string to maxWords (default 10) and the maximum number of
    letters in a word to maxWordLen (default 15).

    Note: this function will strip out newlines and carriage returns and
    remove redundant spaces (i.e. "  " will become " ").

    Raises ValueError if you give it insane values for maxWords and/or 
    maxWordLen."""

    import re

    # Sanity check args
    if ((maxWords < 1) or (maxWordLen < 1)):
        raise ValueError

    # Split the words on whitespace
    wordlist = re.split('\s+', s)

    # If the number of words in the new wordlist exceeded maxWords, whack
    # them and append "....". This denotes that there is more text to follow.
    if (len(wordlist) > maxWords):
        del wordlist[maxWords:]
        wordlist.append('....')

    # Loop over the words in reverse order. If we find a word that is too
    # long, go ahead and truncate the word with "..." and then whack all 
    # words to the right.
    curr = len(wordlist) - 1
    while (curr >= 0):
        if len(wordlist[curr]) > maxWordLen:
            wordlist[curr] = (wordlist[curr])[:maxWordLen] + '...'
            del wordlist[curr+1:]
            break
        curr -= 1

    # Return the new wordlist joined with spaces.
    return ' '.join(wordlist)


def splitVersionForDisplay(s):
    if len(s) < 60:
        return s
    else:
        return s.replace('//', ' //')


def extractBasePath(uri, path_info):
    if path_info == "/":
        return uri
    return uri[:-len(path_info)+1]


def hostPortParse(hostname, defaultPort):
    """ A simple function to split a hostname:port construct, returning
        a 2-tuple of the hostname and port. If the colon specifier isn't in
        the string, then the defaultPort is passed back as the port. """

    if not hostname:
        raise ValueError

    if ':' in hostname:
        (h, p) = hostname.split(':')
    else:
        h = hostname
        p = defaultPort

    return (h, int(p))

def rewriteUrlProtocolPort(url, newProtocol, newPort = None):
    """ Given a URL, rewrites it to point to a different protocol. 
        Optionally rewrites the port if newPort is given. """

    import urlparse

    spliturl = urlparse.urlsplit(url)
    hostname = spliturl[1]

    if newPort:
        if ':' in spliturl[1]:
            hostname = hostname.split(':')[0]

        if ((newProtocol == 'http' and newPort != 80) or  \
            (newProtocol == 'https' and newPort != 443)):
            hostname = "%s:%d" % (hostname, newPort)

    return urlparse.urlunsplit((newProtocol, hostname) + spliturl[2:])

def getArchFromFlavor(flavor):
    fs = ""
    if type(flavor) == str:
        flavor = deps.ThawFlavor(flavor)
    if flavor.members:
        try:
            fs = flavor.members[deps.DEP_CLASS_IS].members.keys()[0]
        except KeyError:
            pass

    return fs

def fixentities(htmltext):
    # replace HTML character entities with numerical references
    # note: this won't handle CDATA sections properly
    def repl(m):
        entity = htmlentitydefs.entitydefs.get(m.group(1).lower())
        if not entity:
            return m.group(0)
        elif len(entity) == 1:
            if entity in "&<>'\"":
                return m.group(0)
            return "&#%d;" % ord(entity)
        else:
            return entity
    return re.sub("&(\w+);?", repl, htmltext)

def getVersionForCacheFakeout():
    """ This version string is used in our webpages where we want to 
        force the Javascript or CSS to reload upon updating rBuilder.
        See mint/web/templates/layout.kid for example usage. """
    return constants.fullVersion

def formatTime(t):
    return time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime(float(t)))

def generateMirrorUserName(rbuilderHostname, updateServiceHostname):
    # Generate a mirrorUser for this rBuilder
    return "-mirroruser-%s-%s" % (rbuilderHostname, updateServiceHostname)

def cleanseUrl(protocol, url):
    if url.find('@') != -1:
        return protocol + '://<user>:<pwd>@' + url.rsplit('@', 1)[1]
    return url

# convert time.time() to timestamp with optional offset
def toDatabaseTimestamp(secsSinceEpoch=None, offset=0):
    """
    Given the number of seconds since the epoch, return a datestamp
    in the following format: YYYYMMDDhhmmss.

    Default behavior is to return a timestamp based on the current time.

    The optional offset parameter lets you retrive a timestamp whose time
    is offset seconds in the past or in the future.

    This function assumes UTC.
    """

    if secsSinceEpoch == None:
        secsSinceEpoch = time.time()

    timeToGet = time.gmtime(secsSinceEpoch + float(offset))
    return long(time.strftime('%Y%m%d%H%M%S', timeToGet))

# and the reverse of the above
def fromDatabaseTimestamp(timeStamp):
    """
    Given a database timestamp generated by toDatabaseTimestamp,
    (e.g. a long int or string in the format YYYYMMDDhhmmss), convert it
    into the number of seconds after the epoch in UTC.
    """
    if isinstance(timeStamp, (int, float)):
        timeStamp = str(long(timeStamp))
    elif isinstance(timeStamp, (unicode, long)):
        timeStamp = str(timeStamp)
    elif isinstance(timeStamp, str):
        pass
    else:
        raise ValueError  # don't know what to do with it

    return (time.mktime(time.strptime(timeStamp, '%Y%m%d%H%M%S')) - \
            (time.localtime().tm_isdst and time.altzone or time.timezone))

def getUrlHost(url):
    """
    Given a URL, pull out the hostname only.
    """
    host = urlparse.urlparse(url)[1]
    if '@' in host:
        host = host[host.find('@')+1:]
    if ':' in host:
        host = host[:host.find(':')]
    return host

LOCAL_CONARY_PROXIES = { 'http': 'http://localhost',
                         'https': 'https://localhost' }
def configureClientProxies(conaryCfg, useInternalConaryProxy,
        httpProxies={}, internalConaryProxies=LOCAL_CONARY_PROXIES):

    from conary import conarycfg
    from mint import config

    if not conaryCfg:
        conaryCfg = conarycfg.ConaryConfiguration()

    if useInternalConaryProxy:
        if 'conaryProxy' in conaryCfg:
            # >= 1.1.24
            conaryCfg.conaryProxy = internalConaryProxies
        elif 'proxy' in conaryCfg:
            # 1.1.17 <=> 1.1.23
            conaryCfg.proxy = internalConaryProxies
        else:
            # noop
            pass
    else:
        if 'proxy' in conaryCfg:
            conaryCfg.proxy = httpProxies

    return conaryCfg

def getProjectText():
    """Returns project if rBO and product if rBA"""
    return isRBO() and "project" or "product"

def genPassword(length):
    """
    @param length: length of random password generated
    @returns: returns a character string of random letters and digits.
    @rtype: str
    """
    choices = string.letters + string.digits
    pw = "".join([random.choice(choices) for x in range(length)])
    return pw

def getBuildIdFromUuid(uuid):
        """
        Get the build id from the specified uuid
        """
        buildId = None
        if uuid:
            chunks = uuid.split("-build-")
            if chunks and chunks[1]:
                parts = chunks[1].split('-')
                if parts:
                    buildId = parts[0]

        return string.atoi(buildId)

def addUserToRepository(repos, username, password, role, label=None):
    """
    Add a user to the repository
    """
    if label:
        try:
            repos.addRole(label, role)
        except RoleAlreadyExists:
            # who cares
            pass
        repos.addUser(label, username, password)
        repos.updateRoleMembers(label, role, [username])
    else:
        try:
            repos.auth.addRole(role)
        except RoleAlreadyExists:
            # who cares
            pass
        repos.auth.addUser(username, password)
        repos.auth.updateRoleMembers(role, [username])

def addUserByMD5ToRepository(repos, username, password, salt, role, label=None):
    """
    Add a user to the repository
    """
    if label:
        try:
            repos.addRole(label, role)
        except RoleAlreadyExists:
            # who cares
            pass
        repos.addUserByMD5(label, username, salt, password)
        repos.updateRoleMembers(label, role, [username])
    else:
        try:
            repos.auth.addRole(role)
        except RoleAlreadyExists:
            # who cares
            pass
        repos.auth.addUserByMD5(username, salt, password)
        repos.auth.updateRoleMembers(role, [username])

