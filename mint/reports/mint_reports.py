#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#

import os
import time

global _reportlab_present
try:
    from reportlab.pdfgen import canvas
    from reportlab.platypus import *
    from reportlab.lib.styles import PropertySet, getSampleStyleSheet, ParagraphStyle
    from reportlab.test.utils import outputfile
    from reportlab.lib import colors
    _reportlab_present = True
except ImportError:
    _reportlab_present = False

import conary
from conary.lib.util import mkstemp, rmtree

class MintReport(object):
    title = "Report Title"
    headers = ()

    employeeIds = (1445, 1, 2, 3, 4, 6, 10, 12, 13, 14, 20, 27, 28,
        29, 31, 32, 34, 37, 38, 43, 44, 47, 50, 51, 57, 1423, 1181,
        1832, 74, 2025, 1657, 91, 221, 311, 1231)

    def __init__(self, db):
        self.db = db
        self.available = _reportlab_present

    def getData(self, *args, **kwargs):
        raise NotImplementedError

    def getReport(self, *args, **kwargs):
        if not self.available:
            raise NotImplementedError
        res = {}
        res['title'] = self.title
        res['headers'] = self.headers
        res['data'] = self.getData(*args, **kwargs)
        res['time'] = time.time()
        return res

    def getPdf(self, *args, **kwargs):
        if not self.available:
            raise NotImplementedError
        data = [self.headers] + self.getData(*args, **kwargs)

        t = Table(data, repeatRows = True)
        headerStyle = [('BACKGROUND', (0, 0), (3, 0), colors.lightsteelblue)]
        t.setStyle(TableStyle(headerStyle))

        styleSheet = getSampleStyleSheet()

        lst = []

        lst.append(Paragraph("""rBuilder Online Activity Report""", styleSheet['Heading1']))
        lst.append(Paragraph(self.title + " as of " + time.ctime(time.time()), styleSheet['Heading2']))
        lst.append(Spacer(18,18))
        lst.append(t)

        fd, tmpDir = mkstemp()
        os.close(fd)
        tmpFile = tmpDir + 'report.pdf'
        SimpleDocTemplate(tmpFile, showBoundary=1).build(lst)
        fd = open(tmpFile)
        data = fd.read()
        fd.close()
        rmtree(tmpDir)
        return data
