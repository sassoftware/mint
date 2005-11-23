#
# Copyright 2005 rPath Inc.
# All Rights Reserved
#

import os

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

global availableReports
if _reportlab_present:
    availableReports = ['new_users']
else:
    availableReports = []

def getAvailableReports():
    return availableReports

import conary
from conary.lib.util import mkstemp, rmtree
import time

class MintReport(object):
    title = "Report Title"
    headers = ()

    def __init__(self, db):
        self.db = db
        self.available = _reportlab_present

    def getData(self):
        raise NotImplementedError

    def getReport(self):
        if not self.available:
            raise NotImplementedError
        res = {}
        res['title'] = self.title
        res['headers'] = self.headers
        res['data'] = self.getData()
        return res

    def getPdf(self):
        if not self.available:
            raise NotImplementedError
        data = [self.headers] + self.getData()

        t = Table(data, repeatRows = True)
        headerStyle = [('BACKGROUND', (0, 0), (3, 0), colors.lightsteelblue)]
        t.setStyle(TableStyle(headerStyle))

        styleSheet = getSampleStyleSheet()

        lst = []

        lst.append(Paragraph("""rBuilder Online Activity Report""", styleSheet['Heading1']))
        lst.append(Paragraph(self.title, styleSheet['Heading2']))
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
