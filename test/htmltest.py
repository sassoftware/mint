#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint.checkhtml import checkHTML, HtmlTagNotAllowed, HtmlParseError

xml = '<?xml version="1.0"?>\n'
wrap = '<div>%s</div>'

good1 = "<b>Hello</b> world."
good2 = "Now is the time for <span class='foo'><b>all<b> <i>good</i></span> men to blah blah blah..."
good3 = "This is a <b>test <i>some</b>html</i>"

bad1 = "I'm a nasty <script />!"
bad2 = "I'm broken.<hr"
bad3 = "<iframe>Hello world!</iframe>"

class HtmlTest(MintRepositoryHelper):

    def excepts(self, call, args, exception, errStr):
        try:
            call(*args)
        except exception:
            pass
        else:
            self.fail(errStr)

    def testGoodHtml(self):
        assert checkHTML(xml + (wrap % good1)), good1
        assert checkHTML(xml + (wrap % good2)), good2
        assert checkHTML(xml + (wrap % good3)), good3

    def testBadHtml(self):
        self.excepts(checkHTML, [xml + (wrap % bad1)], HtmlTagNotAllowed, "html checker allowed tag <script> to pass")
        self.excepts(checkHTML, [xml + (wrap % bad2)], HtmlParseError, "failed to trap parse error")
        self.excepts(checkHTML, [xml + (wrap % bad3)], HtmlTagNotAllowed, "html checker allowed tag <iframe> to pass")

if __name__ == "__main__":
    testsuite.main()
