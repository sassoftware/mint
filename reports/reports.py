#
# Copyright 2005 rPath Inc.
# All Rights Reserved
#

from reportlab.pdfgen import canvas
from reportlab.platypus import *
from reportlab.lib.styles import PropertySet, getSampleStyleSheet, ParagraphStyle
from reportlab.test.utils import outputfile
from reportlab.lib import colors

import conary
import sqlite3
import time

class MintReport:
    title = "Report Title"
    headers = ()

    def __init__(self, dbPath, reportFile):
        self.db = sqlite3.connect(dbPath)
        self.reportFile = reportFile

    def getData(self):
        raise NotImplementedError
    
    def create(self):
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

        print "Creating report %s..." % self.reportFile,
        SimpleDocTemplate(self.reportFile, showBoundary=1).build(lst)
        print "done."
