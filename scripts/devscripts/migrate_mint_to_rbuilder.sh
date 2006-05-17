#!/bin/sh
#
# Migration script used to migrate an rBuilder Appliance from version 1.5.1
# to version 1.6.3.

# Full install label to products repository
INSTALL_LABEL_PATH="products.rpath.com@rpl:devel"
JOBSERVER_VERSION="1.6.3"

OLD_ROOT="/srv/mint"
OLD_CONF="mint.conf"
NEW_ROOT="/srv/rbuilder"
NEW_CONF="rbuilder.conf"
BACKUPDIR="/tmp/rBA-migration.$$"

# sane path for this script
PATH="/bin:/usr/bin:/sbin:/usr/sbin"

# sanity checks ###############################################################

# Gotta be root
if [ `whoami` != 'root' ]; then
    echo "Migration script must be run as root."
    exit 1
fi

# If rBuilder isn't installed, we can't do very much.
if [ ! -d ${NEW_ROOT} -a ! -d ${OLD_ROOT} ]; then
    echo "rBuilder is not installed; nothing to migrate."
    exit 1
fi

# Bail if it appears the migration has already happened.
if [ ! -d ${OLD_ROOT} -a -d ${NEW_ROOT} ]; then
    echo "Migration has already occurred."
    exit 1
fi

# Don't run this on a system where Conary isn't managing the product.
if [ -d ${OLD_ROOT} ]; then
    conary q mint > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo <<EONOTE
Found ${OLD_ROOT}, but rBuilder doesn't appear to be managed
by Conary. You will need to migrate this system manually.
EONOTE
        exit 1
    fi
fi

# start the migration here ####################################################

# update conary (the old school way)
conary update conary conary-repository conary-build conary-policy --resolve
if [ $? -ne 0 ]; then
    echo "WARNING: Conary not updated, you'll have to do this again manually."
    echo "Current version of conary is $(conary --version)"
fi

# backup the configuration files, as Conary may not keep them around
echo "Backing up configuration files to $BACKUPDIR"
[ ! -d $BACKUPDIR ] && mkdir $BACKUPDIR
for cfgfile in ${OLD_ROOT}/*.conf; do
    # strip out reference to maintenanceMode as it causes config to barf
    bn_cfgfile=`basename $cfgfile`
    grep -Ev '^maintenanceMode' $cfgfile > ${BACKUPDIR}/${bn_cfgfile}
done

# shutdown the jobserver
echo "Stopping the rBuilder jobserver"
service rbuilder-isogen stop

# update using conary 
# (NOTE: we have to use the mint redirect trove to get to rbuilder)
echo "Updating rBuilder via Conary"
conary update {mint,mint-web,mint-mailman,mint-isogen,info-isogen}=$INSTALL_LABEL_PATH
if [ $? -ne 0 ]; then
    echo "Problems occurred when updating rBuilder via Conary; exiting"
    exit 1
fi

echo "Updating rbuilder.conf, preserving changes"
# TODO FIXME: we probably need to update the supported image types here
python - <<EOSCRIPT
from mint import config

oldCfg = config.MintConfig()
oldCfg.read('$BACKUPDIR/${OLD_CONF}')

newCfg = config.MintConfig()
newCfg.read('${NEW_ROOT}/${NEW_CONF}')

for k in newCfg.iterkeys():
    if k in oldCfg:
        v = oldCfg[k]
        if isinstance(v, str):
            v = v.replace('${OLD_ROOT}', '${NEW_ROOT}')
            v = v.replace('${OLD_CONF}', '${NEW_CONF}')
        elif isinstance(v, list):
            # ignore non-string items in lists
            try:
                v = [x.replace('${OLD_ROOT}', '${NEW_ROOT}') for x in v]
            except:
                pass
        newCfg[k] = v

newCfgFile = open('${NEW_ROOT}/${NEW_CONF}', 'w')
newCfg.display(out = newCfgFile)
newCfgFile.close()
EOSCRIPT

# restore bits from /srv/mint
echo "Restoring old databases, images, and Conary repositories"
for d in data repos finished-images; do
    mv -u ${OLD_ROOT}/$d/* ${NEW_ROOT}/$d > /dev/null 2>&1
done

# updating rbuilder imagefiles table
echo "Fixing ImageFiles table"
python - <<EOSCRIPT
from conary import dbstore
db = dbstore.connect('${NEW_ROOT}/data/db')
cu = db.cursor()
rs = cu.execute('select fileid, filename from imagefiles')
for id, fn in rs.fetchall():
   cu.execute('update imagefiles set filename = ? where fileid = ?', fn.replace('${OLD_ROOT}', '${NEW_ROOT}'), id)

db.commit()
EOSCRIPT

# remove the SQL caches from repos
echo "Removing stale SQL caches from Conary repositories"
find ${NEW_ROOT}/repos -name cache.sql -exec rm -f {} \;

# update isogen UID
echo "Updating isogen user ID"
old_isogen_uid=`id -u isogen`
new_isogen_uid=104
usermod -u $new_isogen_uid -d /srv/rbuilder/images isogen
find $NEW_ROOT -uid $old_isogen_uid \
    -exec chown $new_isogen_uid {} \; > /dev/null 2>&1

# install chrooted jobserver and start it up
echo "Installing a new chrooted jobserver instance"
/usr/share/rbuilder/scripts/install-jsroot \
    group-jobserver-root=${INSTALL_LABEL_PATH}/${JOBSERVER_VERSION}
if [ $? -ne 0 ]; then
    echo "WARNING: rBuilder jobserver was not installed"
else
    echo "Starting up the rBuilder jobserver"
    service multi-jobserver start
fi

# restart the webserver
echo "Restarting Apache"
killall -USR1 httpd

echo "Done."
exit 0
