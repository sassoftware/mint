#!/bin/sh
#
# Migrate rBA 1.5.3 -> rBA 1.6.3

BACKUPDIR="/tmp/rBA-migration.$$"
INSTALL_LABEL_PATH="rbabeta.devel.org.rpath@rpl:devel"

if [ `whoami` != 'root' ]; then
    echo "Migration script must be run as root."
    exit 1
fi

if [ ! -d /srv/rbuilder -a ! -d /srv/mint ]; then
    echo "rBuilder is not installed; nothing to migrate."
    exit 1
fi

if [ ! -d /srv/mint -a -d /srv/rbuilder ]; then
    echo "Migration has already occurred."
    exit 1
fi

# start the migration here ####################################################

# backup the configuration files, as Conary may not keep them around
echo "Backing up configuration files to $BACKUPDIR"
[ ! -d $BACKUPDIR ] && mkdir $BACKUPDIR
for cfgfile in /srv/mint/*.conf; do
    # strip out reference to maintenanceMode as it causes config to barf
    bn_cfgfile=`basename $cfgfile`
    grep -Ev '^maintenanceMode' $cfgfile > ${BACKUPDIR}/${bn_cfgfile}
done

# update using conary 
# (NOTE: we have to use the mint redirect trove to get to rbuilder)
echo "Updating rBuilder via Conary"
conary update {mint,mint-web,mint-mailman,mint-isogen,info-isogen}=$INSTALL_LABEL_PATH
if [ $? -ne 0 ]; then
    echo "Problems occurred when updating rBuilder via Conary; exiting"
    exit 1
fi

echo "Updating rbuilder.conf, preserving changes"
python - <<EOSCRIPT
from mint import config

oldCfg = config.MintConfig()
oldCfg.read("$BACKUPDIR/mint.conf")

newCfg = config.MintConfig()
newCfg.read('/srv/rbuilder/rbuilder.conf')

for k in newCfg.iterkeys():
    if k in oldCfg:
        v = oldCfg[k]
        if isinstance(v, str):
            v = v.replace('/srv/mint', '/srv/rbuilder')
            v = v.replace('mint.conf', 'rbuilder.conf')
        newCfg[k] = v

newCfgFile = open('/srv/rbuilder/rbuilder.conf', 'w')
newCfg.display(out = newCfgFile)
newCfgFile.close()
EOSCRIPT

echo "Restoring old databases and Conary repositories"
cp -pr /srv/mint/{data,repos} /srv/rbuilder

# remove the SQL caches
echo "Removing stale SQL caches from Conary repositories"
find /srv/rbuilder/repos -name cache.sql -exec rm -f {} \;

# TODO create a chroot here

# restart the webserver
killall -USR1 httpd > /dev/null 2>&1

exit 0
