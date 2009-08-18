#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
from mint_test import mint_rephelp

import os
import socket
import selenium
import time

class SeleniumHelper(mint_rephelp.BaseWebHelper):
    def setUp(self):
        mint_rephelp.BaseWebHelper.setUp(self)

        try:
            seleniumHost = os.environ.get("SELENIUM_HOST", "localhost")
            seleniumPort = os.environ.get("SELENIUM_PORT", "4444")
            seleniumBrowser = os.environ.get("SELENIUM_BROWSER", "*firefox")

            self.s = selenium.selenium(seleniumHost, seleniumPort, seleniumBrowser, self.URL)
            self.s.start()
        except socket.error:
            raise RuntimeError("Please make sure a selenium-server is running on %s:%s." % (seleniumHost, seleniumPort))

    def tearDown(self):
        self.s.stop()
        mint_rephelp.BaseWebHelper.tearDown(self)

    def clickAndWait(self, click, timeout = 10000):
        self.s.click(click)
        self.s.wait_for_page_to_load(timeout)

    def clickAjax(self, locator, accept, timeout = 10000):
        self.s.click(locator)

        for x in range(0, timeout / 100):
            if accept in self.s.get_body_text():
                return
            time.sleep(0.1)

        raise RuntimeError("Script-driven text never appeared: %s" % accept)

