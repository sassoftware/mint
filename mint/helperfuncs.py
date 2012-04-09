#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#

import copy
import htmlentitydefs
import inspect
import os
import re
import random
import string
import time
import traceback
import urlparse
import urllib

from conary import conarycfg
from conary import conaryclient
from conary import versions
from conary.deps import arch, deps
from conary.repository.errors import InsufficientPermission

from mint import config
from mint import constants
from mint import buildtypes
from mint import mint_error


def truncateForDisplay(s, maxWords=10, maxWordLen=15):
    """Truncates a string s for display. May limit the number of words in the
    displayed string to maxWords (default 10) and the maximum number of
    letters in a word to maxWordLen (default 15).

    Note: this function will strip out newlines and carriage returns and
    remove redundant spaces (i.e. "  " will become " ").

    Raises ValueError if you give it insane values for maxWords and/or 
    maxWordLen."""

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

def urlSplit(url, defaultPort = None):
    """A function to split a URL in the format
    <scheme>://<user>:<pass>@<host>:<port>/<path>;<params>#<fragment>
    into a tuple
    (<scheme>, <user>, <pass>, <host>, <port>, <path>, <params>, <fragment>)
    Any missing pieces (user/pass) will be set to None.
    If the port is missing, it will be set to defaultPort; otherwise, the port
    should be a numeric value.
    """
    scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
    userpass, hostport = urllib.splituser(netloc)
    host, port = urllib.splitnport(hostport, None)
    if userpass:
        user, passwd = urllib.splitpasswd(userpass)
    else:
        user, passwd = None, None
    return scheme, user, passwd, host, port, path, \
        query or None, fragment or None

def urlUnsplit(urlTuple):
    """Recompose a split URL as returned by urlSplit into a single string
    """
    scheme, user, passwd, host, port, path, query, fragment = urlTuple
    userpass = None
    if user and passwd:
        userpass = urllib.quote("%s:%s" % (user, passwd), safe = ':')
    hostport = host
    if port:
        hostport = urllib.quote("%s:%s" % (host, port), safe = ':')
    netloc = hostport
    if userpass:
        netloc = "%s@%s" % (userpass, hostport)
    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))

def rewriteUrlProtocolPort(url, newProtocol, newPort = None):
    """ Given a URL, rewrites it to point to a different protocol. 
        Optionally rewrites the port if newPort is given. """

    spliturl = urlparse.urlsplit(url)
    hostname = spliturl[1]

    if newPort:
        if ':' in spliturl[1]:
            hostname = hostname.split(':')[0]

        if ((newProtocol == 'http' and newPort != 80) or  \
            (newProtocol == 'https' and newPort != 443)):
            hostname = "%s:%d" % (hostname, newPort)

    return urlparse.urlunsplit((newProtocol, hostname) + spliturl[2:])


def _getMajorArch(flavor):
    if not isinstance(flavor, deps.Flavor):
        flavor = deps.ThawFlavor(flavor)

    if flavor.members and deps.DEP_CLASS_IS in flavor.members:
        depClass = flavor.members[deps.DEP_CLASS_IS]
        return arch.getMajorArch(depClass.getDeps())

    return None


def getMajorArchFlavor(flavor):
    '''
    Return a new flavor with just the major architecture in I{flavor}.

    @param flavor: A flavor object or a string containing a frozen
                   flavor
    @type flavor: str or unicode or L{conary.deps.Flavor}
    @rtype: L{conary.deps.Flavor}
    '''

    ret = deps.Flavor()
    majorDep = _getMajorArch(flavor)
    if majorDep:
        # Make a copy of the dep before stripping off flags
        shortDep = copy.deepcopy(majorDep)
        shortDep.flags = {}
        ret.addDep(deps.InstructionSetDependency, shortDep)

    return ret


def getArchFromFlavor(flavor):
    '''
    Return the major architecture (e.g. "x86_64") found in I{flavor}.
    
    @param flavor: A flavor object or a string containing a frozen
                   flavor
    @type flavor: str or unicode or L{conary.deps.Flavor}
    @rtype: str
    '''

    majorDep = _getMajorArch(flavor)
    if majorDep:
        return majorDep.name
    else:
        return ''


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

def formatHTTPDate(t=None):
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(t))

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


LOCAL_CONARY_PROXIES = { 'http': 'http://localhost',
                         'https': 'https://localhost' }
def configureClientProxies(conaryCfg, useInternalConaryProxy,
        httpProxies={}, internalConaryProxies=LOCAL_CONARY_PROXIES):

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
    return "product"

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

def collateDictByKeyPrefix(fields, coerceValues=False):
    """
    Take a dict of fields that looks like this:

        { 'prefix-idx1-key1': 'value1', 'prefix-idx2-key2': 'value2', ... ]

    and collate it into a nested dict that looks like this:

        { 'prefix': [{'key1': 'value1', 'key2': 'value2', ... ] }

    Note: this ignores anything that doesn't match the pattern (i.e.
    all keys must be in the form 'prefix-index-value'

    Note: values may contain hyphens, but prefixes cannot!

    Specifying coerceValues as True will coerce all values to Strings.
    """
    dicts = {}
    for key, value in sorted(fields.iteritems()):
        try:
            # Split on prefix-index-key. Prefix cannot contain
            # any hyphens!
            prefix, index, name = key.split('-', 2)
            index = int(index)
        except ValueError:
            # ignore anything that doesn't conform
            continue
        pd = dicts.setdefault(prefix, {})
        d = pd.setdefault(index, {})
        if coerceValues:
            value = str(value)
        d[name] = value

    for key, value in dicts.iteritems():
        value = [ x[1] for x in sorted(value.iteritems()) ]
        dicts[key] = value


    return dicts


def getProductVersionDefaultStagesNames():
    """
    Build a list containing the default stage names
    """
    names = []
    stagesList = getProductVersionDefaultStagesList()
    for stage in stagesList:
        names.append(stage['name'])
        
    return names

def getProductVersionDefaultStage():
    """
    Get the default stage 
    """
    return dict(name='Development', labelSuffix='-devel')

def getProductVersionDefaultStagesList():
    """
    Build a list containing the default stages
    """       
    defaultStage = getProductVersionDefaultStage() 
    return [defaultStage,
            dict(name='QA',
                 labelSuffix='-qa'),
            dict(name='Release',
                 labelSuffix='')]
        
def addDefaultStagesToProductDefinition(productDefinitionObj):
    """
    Given a product definition object, add the canned set of
    stages to it. This function modifies the original object.
    """
    for stage in getProductVersionDefaultStagesList():
        productDefinitionObj.addStage(stage['name'],
                stage['labelSuffix'])
    return

def addDefaultPlatformToProductDefinition(productDefinition):
    """
    Given a product definition object, add the canned platform defaults
    to it, if needed. This function does nothing if any architectures,
    flavorSets, containerTemplates or buildTemplates are defined. This
    function modifies the original object
    """
    from rpath_proddef import api1 as proddef
    # XXX don't use the internal interface here
    productDefinition._ensurePlatformExists()
    if not (productDefinition.getArchitectures() or
            productDefinition.getFlavorSets() or
            productDefinition.getContainerTemplates() or
            productDefinition.getBuildTemplates() or
            productDefinition.platform.getArchitectures() or
            productDefinition.platform.getFlavorSets() or
            productDefinition.platform.getContainerTemplates() or
            productDefinition.platform.getBuildTemplates()):
        proddef._addPlatformDefaults(productDefinition.platform)

def getDefaultImageGroupName(shortname):
    """
    Given the project's shortname, give the default image group name
    (e.g. group-<shortname>-appliance).
    """
    if not shortname:
        raise mint_error.MintError("Shortname missing when trying to determine default image group name")
    return 'group-%s-appliance' % shortname

def sanitizeProductDefinition(projectName, projectDescription,
        repositoryHostname, shortname, version,
        versionDescription, namespace, productDefinition=None):
    """
    Sanitize a product definition object to make sure that 
    bits filled in by rBuilder are appropriately set.
    If a productDefinition object isn't passed in, one is
    created and returned.
    """
    from rpath_proddef import api1 as proddef
    if not productDefinition:
        productDefinition = proddef.ProductDefinition()
    productDefinition.setProductName(projectName)
    productDefinition.setProductDescription(projectDescription)
    productDefinition.setProductShortname(shortname)
    productDefinition.setProductVersion(version)
    productDefinition.setProductVersionDescription(versionDescription)
    productDefinition.setConaryNamespace(namespace)
    productDefinition.setConaryRepositoryHostname(repositoryHostname)
    productDefinition.setImageGroup(getDefaultImageGroupName(shortname))

    addDefaultStagesToProductDefinition(productDefinition)

    addDefaultPlatformToProductDefinition(productDefinition)

    return productDefinition

def validateNamespace(ns):
    """
    Validate a namespace
    @param ns: a namespace to validate
    @return: True if valid, else a string explaining what is wrong
    """
    if len(ns) > 16:
        return "The namespace cannot be more than 16 characters long"

    valid = ns and "@" not in ns and ':' not in ns
    if not valid:
        return "The namespace can not contain '@' or ':'."
    
    return True


def weak_signature_call(_func, *args, **kwargs):
    '''
    Call I{func} with keyword arguments I{kwargs}, removing any keyword
    arguments not expected by I{func}.
    '''

    # Iterate down the chain of decorators until we hit the actual
    # function
    target_func = _func
    while hasattr(target_func, '__wrapped_func__'):
        target_func = target_func.__wrapped_func__

    argnames, _, varkw, _ = inspect.getargspec(target_func)
    if varkw:
        # We can't guess what variable keywords are in use, so just pass
        # them on. With any luck, the function will not care about extras
        # in a dictionary.
        keep_args = kwargs
    else:
        keep_args = dict((arg, value) for (arg, value) in kwargs.iteritems()
            if arg in argnames)
    return _func(*args, **keep_args)

def formatProductVersion(versions, currentVersion):
    if currentVersion is None:
        return "Not Selected"
    ret = None
    namespaces = dict()
    for vId, b, ns, ver, nada in versions:
        namespaces[ns] = 1
        if vId == currentVersion:
            ret = (ns, ver)
    if not ret:
        raise RuntimeError("Could not find the current version in the version list")
    showNamespace = len(namespaces.keys()) > 1
    if showNamespace:
        ret = "%s (%s)" % (ret[1], ret[0])
    else:
        ret = "%s" % ret[1]
    return ret

def getBasicConaryConfiguration(mintCfg):
    """ Return a basic conary client configuration. """


    ccfg = conarycfg.ConaryConfiguration()
    conarycfgFile = os.path.join(mintCfg.dataPath, 'config', 'conaryrc')
    if os.path.exists(conarycfgFile):
        ccfg.read(conarycfgFile)
    ccfg.dbPath = ':memory:'
    ccfg.root   = ':memory:'
    ccfg = configureClientProxies(ccfg, mintCfg.useInternalConaryProxy, mintCfg.proxy, mintCfg.getInternalProxies())
    return ccfg


def parseFlavor(fStr):
    """
    Try to parse C{fStr} as a frozen or stringified flavor.
    """
    # This is a little fuzzy...
    if not fStr:
        return deps.Flavor()

    if '#' in fStr and fStr[:fStr.find('#')].isdigit():
        return deps.ThawFlavor(fStr)

    return deps.parseFlavor(fStr)


def parseVersion(vStr):
    """
    Try to parse C{vStr} as a version with or without timestamps.
    """
    try:
        return versions.ThawVersion(vStr)
    except:
        pass

    try:
        return versions.VersionFromString(vStr)
    except:
        pass

    return None


def setCurrentProductVersion(session, projectId, versionId):
    '''
    Set the current product version
    @param session -- the current session object
    @param projectId -- the id of the project
    @param versionId -- the id of the version
    '''
    session.setdefault('currentVersion', {})[projectId] = versionId
    session.save()
