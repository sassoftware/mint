#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
import unittest
testsuite.setup()

from mint.checkhtml import checkHTML, HtmlTagNotAllowed, HtmlParseError

xml = '<?xml version="1.0"?>\n'
wrap = '<div>%s</div>'

good1 = "<b>Hello</b> world."
good2 = "Now is the time for <span class='foo'><b>all</b> <i>good</i></span> men to blah blah blah..."
good3 = "This is a <b>test <i>some</i> html</b>"

bad1 = "I'm a nasty <script />!"
bad2 = "I'm broken.<hr"
bad3 = "<iframe>Hello world!</iframe>"

class HtmlTest(unittest.TestCase):
    def testGoodHtml(self):
        assert checkHTML(xml + (wrap % good1)), good1
        assert checkHTML(xml + (wrap % good2)), good2
        assert checkHTML(xml + (wrap % good3)), good3

    def testBadHtml(self):
        self.assertRaises(HtmlTagNotAllowed, checkHTML, xml + (wrap % bad1))
        self.assertRaises(HtmlParseError, checkHTML, xml + (wrap % bad2))
        self.assertRaises(HtmlTagNotAllowed, checkHTML, xml + (wrap % bad3))

if __name__ == "__main__":
    testsuite.main()
