#
# Copyright (c) 2007 rPath, Inc.
#
# All Rights Reserved
#
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.barcharts import HorizontalBarChart

from conary import dbstore
from conary.dbstore import sqllib
import time
import tempfile
import os

DAY = 3600 * 24

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

    def getData(self, projectId):
        data = []
        labels = []

        cu = self._db.cursor()

        now = time.time()
        for x in range(self._span, 0, -1):
            print x
            start = now - (x * self._interval)
            end = now - ((x - 1) * self._interval)

            print start, end
            cu.execute("""SELECT COUNT(ip) FROM UrlDownloads
                JOIN FilesUrls USING(urlId)
                JOIN BuildFilesUrlsMap USING (urlId)
                JOIN BuildFiles USING (fileId)
                JOIN Builds USING (buildId)
                WHERE projectId=? AND timeDownloaded <= ? AND timeDownloaded >= ?""",
                    self._projectId, sqllib.toDatabaseTimestamp(end), sqllib.toDatabaseTimestamp(start))
            data.append(cu.fetchone()[0])
            labels.append(time.strftime("%Y-%m-%d", time.gmtime(start)))

        return [data], labels

    def getImageData(self, format = 'png'):
        fd, fn = tempfile.mkstemp(suffix = '.' + format)
        data = None
        try:
            os.close(fd)
            self.save(formats=[format], outDir = os.path.dirname(fn), fnRoot = fn[:-4])
            f = open(fn)
            data = f.read()
            f.close()
        finally:
            os.unlink(fn)
        return data
