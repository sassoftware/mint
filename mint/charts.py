#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.barcharts import HorizontalBarChart

from reportlab.lib import colors

from conary import dbstore
from mint import helperfuncs
import time
import tempfile
import os

DAY = 3600 * 24

from reportlab.graphics import renderPM
from reportlab.graphics import renderSVG
from reportlab.graphics import renderPDF

formatDict = {
    'png': renderPM,
    'svg': renderSVG,
    'pdf': renderPDF,
}

rPathLightBlue = colors.HexColor(0x5d82b7)

class DownloadChart(Drawing):
    def __init__(self, db, projectId, interval = DAY, span = 7, width=600, height=400, *args, **kw):
        self._db = db
        self._projectId = projectId
        self._interval = interval
        self._span = span

        apply(Drawing.__init__,(self,width,height)+args,kw)
        self.add(VerticalBarChart(), name='chart')

        self.add(String(20, 380, 'Daily Downloads (last %d days)' % self._span), name='title')

        self.chart.x = 20
        self.chart.y = 60
        self.chart.width = self.width - 30
        self.chart.height = self.height - 90


        self.title.fontName = 'Helvetica-Bold'
        self.title.fontSize = 12

        self.chart.barLabelFormat = "%d"
        self.chart.barLabels.dx = 0
        self.chart.barLabels.dy = 10

        self.chart.data, labels = self.getData(13)

        self.chart.categoryAxis.categoryNames = labels
        self.chart.categoryAxis.labels.angle = 60
        self.chart.categoryAxis.labels.boxAnchor= "se"
        self.chart.categoryAxis.labels.dy = -10

        self.chart.valueAxis.valueMax = max(self.chart.data[0]) + 10
        self.chart.valueAxis.valueMin = 0

        self.chart.bars[0].fillColor = rPathLightBlue

    def getData(self, projectId):
        data = []
        labels = []

        cu = self._db.cursor()

        now = time.time()
        for x in range(self._span, 0, -1):
            start = now - (x * self._interval)
            end = now - ((x - 1) * self._interval)

            cu.execute("""SELECT COUNT(ip) FROM UrlDownloads
                JOIN FilesUrls USING(urlId)
                JOIN BuildFilesUrlsMap USING (urlId)
                JOIN BuildFiles USING (fileId)
                JOIN Builds USING (buildId)
                WHERE projectId=? AND timeDownloaded <= ? AND timeDownloaded >= ?""",
                    self._projectId, helperfuncs.toDatabaseTimestamp(end), helperfuncs.toDatabaseTimestamp(start))
            data.append(cu.fetchone()[0])
            labels.append(time.strftime("%Y-%m-%d", time.gmtime(start)))

        return [data], labels

    def getImageData(self, format = 'png'):
        renderer = formatDict[format]
        if renderer == renderPM:
            d = renderer.drawToString(self, format)
        else:
            d = renderer.drawToString(self)

        return d
