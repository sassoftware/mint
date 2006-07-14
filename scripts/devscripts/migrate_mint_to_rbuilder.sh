#!/bin/sh
#
# Migration script used to migrate an rBuilder Appliance from version 1.5.1
# to version 1.6.3.

# Full install label to builds repository
INSTALL_LABEL_PATH="builds.rpath.com@rpath:rba-1.6"
JOBSERVER_VERSION="1.6.3"

OLD_ROOT="/srv/mint"
OLD_CONF="mint.conf"
NEW_ROOT="/srv/rbuilder"
NEW_CONF="rbuilder.conf"
BACKUPDIR="/tmp/rBA-migration.$$"

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

# Don't run this on a system where Conary isn't managing the build.
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

# whack builds line from conaryrc
echo "Updating conaryrc"
sed -i.bak -e 's/builds.rpath.com@.* //g' /etc/conaryrc

# update conary (the old school way)
echo "Updating Conary"
conary update {conary,conary-repository,conary-build}=1.0.18 conary-policy --resolve
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

# shutdown the webserver
echo "Stopping Apache"
service httpd stop
sleep 3
# make sure it's dead
killall httpd > /dev/null 2>&1
sleep 3
killall -9 httpd > /dev/null 2>&1

# whack all precompiled python files
echo "Cleaning out stale .pyc/.pyo files"
find /usr/lib/python2.4/site-packages/mint -name \*.py[co] -exec rm -f {} \;

# update using conary 
# use conary migrate to break branch affinity and start fresh
echo "Updating rBuilder via Conary"
conary migrate group-rbuilder-dist=$INSTALL_LABEL_PATH --resolve
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

# tarball and raw FS image added in this release
newCfg.visibleImageTypes.extend([3, 5])

newCfgFile = open('${NEW_ROOT}/${NEW_CONF}', 'w')
newCfg.display(out = newCfgFile)
newCfgFile.close()
EOSCRIPT

# restore bits from /srv/mint
echo "Restoring old databases, images, and Conary repositories"
for d in data repos finished-images; do
    mv ${OLD_ROOT}/$d/* ${NEW_ROOT}/$d > /dev/null 2>&1
done
sync

# prime the cache.sql files in each repository
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
db = dbstore.connect('${NEW_ROOT}/data/db')
cu = db.cursor()
rs = cu.execute('select fileid, filename from imagefiles')
for id, fn in rs.fetchall():
   cu.execute('update imagefiles set filename = ? where fileid = ?', fn.replace('${OLD_ROOT}', '${NEW_ROOT}'), id)

db.commit()
EOSCRIPT

# update isogen UID/GID
echo "Updating isogen user ID and group ID"
old_isogen_uid=`id -u isogen`
new_isogen_uid=104
groupmod -g $new_isogen_uid isogen
usermod -u $new_isogen_uid -g $new_isogen_uid -d ${NEW_ROOT}/images isogen
find $NEW_ROOT -uid $old_isogen_uid \
    -exec chown $new_isogen_uid {} \; > /dev/null 2>&1
find $NEW_ROOT -gid $old_isogen_uid \
    -exec chgrp $new_isogen_uid {} \; > /dev/null 2>&1

# remove old cached changesets
echo "Remove old cached changesets"
find ${NEW_ROOT}/repos -maxdepth 3 -type f -name \*ccs\* -print -exec rm -f {} \;

# migrate old conaryrc for rbuilder
if [ -f ${OLD_ROOT}/conaryrc ]; then
    echo "Migrating conaryrc for rbuilder"
    [ ! -d ${NEW_ROOT}/config ] && mkdir ${NEW_ROOT}/config
    cp ${OLD_ROOT}/conaryrc ${NEW_ROOT}/config/conaryrc
fi

# JS Root was installed by group-rbuilder-dist via jobserver-root trove
# that trove can be deleted; future updates should be done via
# conary update group-jobserver-root
echo "Erasing jobserver install remnants"
conary erase jobserver-root

echo "Starting up the rBuilder jobserver"
service multi-jobserver start

# restart the webserver
echo "Starting Apache"
service httpd start

# move the vestigial remains of /srv/mint to the migration tempdir
echo "Storing leftovers from the migration in $BACKUPDIR/mint.old"
mv $OLD_ROOT $BACKUPDIR/mint.old

echo "Done"
exit 0
