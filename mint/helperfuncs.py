
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#

from conary import versions
from conary.deps import arch, deps
from conary.repository import shimclient
from conary.repository.errors import RoleAlreadyExists
from conary.repository.netrepos import netserver

from mint import constants
from mint import buildtypes
from mint.config import isRBO
from mint.mint_error import MintError

from rpath_common.proddef import api1 as proddef

import copy
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


def _getShimServer(repos):
    # Delete me as soon as addUserToRepository and addUserByMD5ToRepository
    # can safely use a shim to add users to a role. (CNY-2862)

    if isinstance(repos, (shimclient.NetworkRepositoryServer,
      netserver.NetworkRepositoryServer)):
        return repos
    elif isinstance(repos, shimclient.ShimNetClient):
        return repos.c._server._server
    else:
        raise TypeError("Don't know how to get repository from %r" % repos)


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
        # XXX: This is WRONG, but conary offers no API to either add a
        # user or to get the list of users for a role! Instead, we end
        # up blowing away any other members of the role.
        repos.updateRoleMembers(label, role, [username])
    else:
        repos = _getShimServer(repos)
        try:
            repos.auth.addRole(role)
        except RoleAlreadyExists:
            # who cares
            pass
        repos.auth.addUser(username, password)
        repos.auth.addRoleMember(role, username)

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
        # XXX: This is WRONG, but conary offers no API to either add a
        # user or to get the list of users for a role! Instead, we end
        # up blowing away any other members of the role.
        repos.updateRoleMembers(label, role, [username])
    else:
        repos = _getShimServer(repos)
        try:
            repos.auth.addRole(role)
        except RoleAlreadyExists:
            # who cares
            pass
        repos.auth.addUserByMD5(username, salt, password)
        repos.auth.addRoleMember(role, username)


def deleteUserFromRepository(repos, username, label=None, deleteRole=True):
    """
    Delete a user C{username} from repository C{repos} and (maybe) try
    to delete the role of the same name (if present). C{repos} can be
    either a repository client or a repository server; in the former
    case a C{label} is required to identify which repository the user
    will be deleted from.

    @param repos: Repository to delete the user from
    @type  repos: C{NetworkRepositoryClient} or C{NetworkRepositoryServer}
    @param username: Which user to delete
    @type  username: str
    @param label: Label or hostname of the repository to delete the
                  user from, if C{repos} is a
                  C{NetworkRepositoryClient}
    @type  label: str or L{Label<conary.versions.Label>}
    @param deleteRole: If C{True} (the default), try to delete the role
                       of the same name
    @type  deleteRole: bool
    """

    if label:
        repos.deleteUserByName(label, username)
        if deleteRole:
            try:
                repos.deleteRole(label, username)
            except RoleNotFound:
                # Conary deleted the role for us (probably)
                pass
    else:
        repos = _getShimServer(repos)
        repos.auth.deleteUserByName(username)
        if deleteRole:
            try:
                repos.auth.deleteRole(username)
            except RoleNotFound:
                # Conary deleted the role for us (probably)
                pass


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
        
def getBuildDefsAvaliableBuildTypes(allBuildTypes):
    """
    Get a list of the available build types for build defs
    """
    # get the build types to allow
    #    remove online update builds (i.e. imageless)
    allBuildTypes.remove(buildtypes.IMAGELESS)
        
    return allBuildTypes

def addDefaultStagesToProductDefinition(productDefinitionObj):
    """
    Given a product definition object, add the canned set of
    stages to it. This function modifies the original object.
    """
    for stage in getProductVersionDefaultStagesList():
        productDefinitionObj.addStage(stage['name'],
                stage['labelSuffix'])
    return

def getDefaultImageGroupName(shortname):
    """
    Given the project's shortname, give the default image group name
    (e.g. group-<shortname>-appliance).
    """
    if not shortname:
        raise MintError("Shortname missing when trying to determine default image group name")
    return 'group-%s-appliance' % shortname

def sanitizeProductDefinition(projectName, projectDescription,
        hostname, domainname, shortname, version,
        versionDescription, namespace, productDefinition=None):
    """
    Sanitize a product definition object to make sure that 
    bits filled in by rBuilder are appropriately set.
    If a productDefinition object isn't passed in, one is
    created and returned.
    """
    if not productDefinition:
        productDefinition = proddef.ProductDefinition()
    productDefinition.setProductName(projectName)
    productDefinition.setProductDescription(projectDescription)
    productDefinition.setProductShortname(shortname)
    productDefinition.setProductVersion(version)
    productDefinition.setProductVersionDescription(versionDescription)
    productDefinition.setConaryNamespace(namespace)
    productDefinition.setConaryRepositoryHostname("%s.%s" % \
            (shortname, domainname))
    productDefinition.setImageGroup(getDefaultImageGroupName(shortname))

    addDefaultStagesToProductDefinition(productDefinition)

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
