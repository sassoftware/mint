#!/bin/sh

mkdir /tmp/logs/
pushd /tmp/logs

cp /var/log/httpd/access_log /var/log/httpd/access_log.1.gz /var/log/httpd/access_log.2.gz .
gunzip *.gz
grep -h downloadImage access_log.2 access_log.1 access_log > full_access_log

# if this script is run on Monday, we want to start our report on the last Sunday
# morning and end on the Saturday night.

startDate=$(perl -e 'use Date::Manip; print UnixDate(ParseDate("sunday 2 weeks ago"), "%Y-%m-%d")')
endDate=$(perl -e 'use Date::Manip; print UnixDate(ParseDate("last saturday"), "%Y-%m-%d");')
output=/srv/www/html/download-stats/downloads-$(date +%Y-%m-%d).pdf

echo Processing downloads from $startDate $endDate to $output

python /usr/share/rbuilder/scripts/parse-download-logs.py full_access_log $startDate $endDate | a2ps -o - -R -B --rows=1 --columns=1 | ps2pdf - - > $output

popd
rm -rf /tmp/logs/
