#!/bin/sh
#
# Migration script used to migrate a rBuilder Online

# Full install label to products repository
INSTALL_LABEL_PATH="products.rpath.com@rpl:internal"
JOBSERVER_VERSION="1.6.3"

OLD_ROOT="/srv/mint"
OLD_CONF="mint.conf"
NEW_ROOT="/srv/rbuilder"
NEW_CONF="rbuilder.conf"
BACKUPDIR="/tmp/mint-online-migration.$$"

# TODO this should be changed based on where we're running this (shemp vs. live)
DB_CONNECT_STR="rbuilder@db1.cogent-dca.rpath.com/mint"

# apache uid/gid
APACHE_UID=`id -u apache`
APACHE_GID=`id -g apache`

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
        cat - <<EONOTE
Found ${OLD_ROOT}, but rBuilder doesn't appear to be managed
by Conary. You will need to migrate this system manually.
EONOTE
        exit 1
    fi
fi

# start the migration here ####################################################

# update conary (the old school way)
echo "Updating Conary"
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

# shutdown the webserver
echo "Stopping Apache"
service httpd stop
sleep 3
# make sure it's dead
killall httpd > /dev/null 2>&1
sleep 3
killall -9 httpd > /dev/null 2>&1

# TODO test to see if this is necessary (probably not)
# whack all precompiled python files
#echo "Cleaning out stale .pyc/.pyo files"
#find /usr/lib/python2.4/site-packages/mint -name \*.py[co] -exec rm -f {} \;

# update using conary 
echo "Updating rBuilder via Conary"
conary update mint-online=$INSTALL_LABEL_PATH --resolve
if [ $? -ne 0 ]; then
    echo "Problems occurred when updating rBuilder via Conary; exiting"
    exit 1
fi

echo "Updating rbuilder.conf, preserving changes"
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

# tarball added in this release
newCfg.visibleImageTypes.extend([3])

newCfgFile = open('${NEW_ROOT}/${NEW_CONF}', 'w')
newCfg.display(out = newCfgFile)
newCfgFile.close()
EOSCRIPT

# restore bits from /srv/mint

rmdir ${NEW_ROOT}/changesets && ln -s /data/mint/images/changesets \
    ${NEW_ROOT}/changesets
rmdir ${NEW_ROOT}/contents   && ln -s /data/mint/repos-nas2-vol2 \
    ${NEW_ROOT}/contents
rmdir ${NEW_ROOT}/finished-images && ln -s /data/mint/images/finished-images \
    ${NEW_ROOT}/finished-images
rmdir ${NEW_ROOT}/images && ln -s /data/mint/images ${NEW_ROOT}/images

# prime the cache.sql files in each repository (if they don't exist)
python - <<EOSCRIPT
import os
from conary.repository.netrepos import cacheset
for r in os.listdir('${NEW_ROOT}/repos'):
    if os.path.isdir(os.path.join('${NEW_ROOT}', 'repos', r)):
        if not os.path.exists(os.path.join('${NEW_ROOT}', 'repos', \
            r, 'cache.sql')):
            cacheset.CacheSet(('sqlite', os.path.join('${NEW_ROOT}', \
                'repos', r, 'cache.sql')), None)
            os.chown(os.path.join('${NEW_ROOT}', 'repos', r, 'cache.sql'),
                ${APACHE_UID}, ${APACHE_GID})
            print "Created CacheSet for %s\n" % r
EOSCRIPT

# updating rbuilder imagefiles table
echo "Fixing ImageFiles table"
python - <<EOSCRIPT
from conary import dbstore
db = dbstore.connect('${DB_CONNECT_STR}', 'mysql')
cu = db.cursor()
rs = cu.execute('select fileid, filename from imagefiles')
for id, fn in rs.fetchall():
   cu.execute('update imagefiles set filename = ? where fileid = ?', fn.replace('${OLD_ROOT}', '${NEW_ROOT}'), id)
db.commit()
EOSCRIPT

# restart the webserver
#echo "Starting Apache"
#service httpd start

# move the vestigial remains of /srv/mint to the migration tempdir
echo "Storing leftovers from the migration in $BACKUPDIR/mint.old"
mv $OLD_ROOT $BACKUPDIR/mint.old

echo "Done"
exit 0
