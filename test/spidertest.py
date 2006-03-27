#!/usr/bin/python2.4
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
testsuite.setup()

import mint_rephelp
from mint_rephelp import MINT_PROJECT_DOMAIN, MINT_DOMAIN

import os, sys
import tempfile
import re

scriptPath = os.path.join(os.path.split(os.path.split( \
    os.path.realpath(__file__))[0])[0], 'scripts')

class BrokenLink(Exception):
    def __str__(self):
        return self.msg

    def __init__(self, msg = "Broken Link"):
        self.msg = msg

class SpiderPageTest(mint_rephelp.WebRepositoryHelper):
    def stripString(self, baseStr):
        return self.reString.findall(baseStr)[0][1:-1]

    def checkForms(self, page):
        forms = self.reForms.findall(page.body)
        actions = [(self.stripString(self.reAction.findall(x)[0]), \
                    self.stripString(self.reMethod.findall(x)[0]).upper())
                   for x in forms]
        res = self.checkLinks([x[0] for x in actions], page.url)
        for link, index in [(x[0], i) for i, x in \
                            zip(range(len(actions)), actions) if x[1]=='GET']: 
            newPage = page.getForm(index, self.get, {})
            if link not in self.checked:
                res = self.spiderLink(link, newPage) or res
        return res

    def checkLinks(self, links, link):
        brokenLinks = False
        for newLink in links:
            relativeLink = False
            valid = False
            if newLink.startswith('#'):
                # ignore "#" links
                pass
            else:
                valid = True
                skip = False
                if newLink.startswith('/'):
                    relativeLink = True
                if not relativeLink and MINT_DOMAIN not in newLink \
                       and MINT_PROJECT_DOMAIN not in newLink:
                    # silently ignore pages outside our domain.
                    valid = False
                    skip = True
                if 'corp' in newLink:
                    # silently ignore corp pages
                    valid = False
                    skip = True
                    if relativeLink:
                        print "corp link: %s is relative on page: %s" % \
                              (newLink, link)
                        brokenLinks = True
                if not skip and not relativeLink and \
                       str(self.port) not in newLink \
                       and str(self.securePort) not in newLink:
                    print "%s is missing port on page %s" % (newLink, link)
                    valid = False
                    brokenLinks = True
                if not skip and self.mintCfg.basePath not in newLink:
                    print "%s is missing basepath on page %s" % (newLink, link)
                    valid = False
                    brokenLinks = True
            if valid:
                if newLink not in self.checked:
                    try:
                        brokenLinks = self.spiderLink(newLink) or brokenLinks
                    except BrokenLink:
                        print "%s is broken on page: %s" % (newLink, link)
                        brokenLinks = True
        return brokenLinks

    def spiderLink(self, link, page = None):
        self.checked.append(link)
        # print "link:", link
        if page is None:
            try:
                page = self.fetch(link)
            except:
                import epdb
                epdb.st()
                raise BrokenLink("Broken Link: %s" % link)
        # find all html anchors
        links = self.reLinks.findall(page.body)
        # strip cruft.
        links = [self.stripString(x) for x in links]
        brokenLinks = self.checkLinks(links, link) or self.checkForms(page)
        return brokenLinks

    def testBrokenLinks(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = self.newProject(client)
        project = client.getProject(projectId)
        self.moveToServer(project, 1)

        self.addComponent('testcase:source', '1.0.0')
        self.addComponent('testcase:runtime', '1.0.0')
        self.addCollection('testcase', '1.0.0', ['testcase:runtime'])

        fd, fn = tempfile.mkstemp()
        os.close(fd)

        f= open(fn ,'w')
        self.mintCfg.display(f)
        f.close()

        upi = os.path.join(scriptPath, 'update-package-index')
        try:
            self.captureOutput(os.system, "%s %s" % (upi, fn))
        finally:
            os.unlink(fn)

        # compile regex expressions
        self.reLinks = re.compile("<a href=[^<>]*>", re.IGNORECASE)
        self.reForms = re.compile('<form[^<>]*>', re.IGNORECASE)
        self.reString = re.compile("""['"][^'"]*['"]""")
        self.reAction = re.compile("""action=['"][^'"]*['"]""", re.IGNORECASE)
        self.reMethod = re.compile("""method=['"][^'"]*['"]""", re.IGNORECASE)
        #end regex expressions

        self.checked = []
        self.failIf(self.spiderLink(self.mintCfg.basePath),
                    "There are broken links in the site for anonymous users.")

        self.webLogin('foouser', 'foopass')

        self.checked = []
        self.failIf(self.spiderLink(self.mintCfg.basePath),
                    "There are broken links in the site for logged-in users.")

    def testCommitTimestamps(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = self.newProject(client)
        project = client.getProject(projectId)
        self.moveToServer(project, 1)

        self.addComponent('testcase:source', '1.0.0')
        self.addComponent('testcase:runtime', '1.0.0')
        self.addCollection('testcase', '1.0.0', ['testcase:runtime'])

        fd, fn = tempfile.mkstemp()
        os.close(fd)

        f= open(fn ,'w')
        self.mintCfg.display(f)
        f.close()

        upi = os.path.join(scriptPath, 'update-package-index')
        try:
            self.captureOutput(os.system, "%s %s" % (upi, fn))
        finally:
            os.unlink(fn)

        self.failIf(project.getCommits() != project.getCommits(),
                    "getCommits results are not constant. This will trigger "
                    "recursion for spiders.")


if __name__ == "__main__":
    testsuite.main()
