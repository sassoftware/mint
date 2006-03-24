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
    def spiderLink(self, link, page = None):
        self.checked.append(link)
        #print "link:", link
        if page is None:
            try:
                page = self.fetch(link)
            except:
                raise BrokenLink("Broken Link: %s" % link)
        # find all html anchors
        links = re.findall("<a href=[^<>]*>", page.body)
        # strip cruft.
        links = [re.findall("""['"][^'"]*['"]""", x)[0][1:-1] for x in links]
        brokenLinks = False
        for newLink in links:
            valid = False
            if newLink.startswith('#'):
                # ignore "#" links
                pass
            elif newLink.startswith('/'):
                if self.mintCfg.basePath not in newLink:
                    print "%s is missing basepath on page %s" % (newLink, link)
                    brokenLinks = True
                else:
                    valid = True
            else:
                valid = True
                skip = False
                if MINT_DOMAIN not in newLink \
                       and MINT_PROJECT_DOMAIN not in newLink:
                    # silently ignore pages outside our domain.
                    valid = False
                    skip = True
                if 'corp' in newLink:
                    # silently ignore corp pages
                    valid = False
                    skip = True
                if not skip and str(self.port) not in newLink \
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
                        brokenLinks = brokenLinks or self.spiderLink(newLink)
                    except BrokenLink:
                        print "%s is broken on page: %s" % (newLink, link)
                        brokenLinks = True
        return brokenLinks

    def testRebase(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = self.newProject(client)

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

        self.checked = []
        self.failIf(self.spiderLink(self.mintCfg.basePath),
                    "There are broken links in the site.")


if __name__ == "__main__":
    testsuite.main()
