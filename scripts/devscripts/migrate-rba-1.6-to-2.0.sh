#!/bin/sh
#
# Migration script used to migrate an rBuilder Appliance from version 1.6.3
# to version 2.0.0

# Full install label to builds repository
INSTALL_LABEL_PATH="products.rpath.com@rpath:rba-devel"

RBUILDER_ROOT="/srv/rbuilder"
BACKUPDIR="/tmp/rBA-2.0-migration.$$"

# sane path for this script
PATH="/bin:/usr/bin:/sbin:/usr/sbin"

# sanity checks ###############################################################

# Gotta be root
if [ `whoami` != 'root' ]; then
    echo "Migration script must be run as root."
    exit 1
fi

# If rBuilder isn't installed, we can't do very much.
if [ ! -d ${RBUILDER_ROOT} ]; then
    echo "rBuilder is not installed; nothing to migrate."
    exit 1
fi

# Check to see if the installed group-rbuilder-dist is indeed == 1.6.3
curr_ver=`conary q group-rbuilder-dist | cut -d'=' -f2 | cut -d'-' -f1`
case $curr_ver in
    1.6.3)
        echo "Found version 1.6.3 of group-rbuilder-dist. Migration proceeding."
        ;;
    2.0.0)
        echo "Migration has already taken place. Exiting."
        exit 1
        ;;
    *)
        echo "Migration script will only migrate version 1.6.3 to version 2.0.0."
        echo "Currently installed version: \"${curr_ver}\"."
        exit 1
        ;;
esac

if [ -d ${RBUILDER_ROOT} ]; then
    conary q rbuilder > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        cat - <<EONOTE
Found ${RBUILDER_ROOT}, but rBuilder doesn't appear to be managed
by Conary. You will need to migrate this system manually.
EONOTE
        exit 1
    fi
fi

# start the migration here ####################################################

# update conary (the old school way)
echo "Updating Conary to 1.0.27"
conary update {conary,conary-repository,conary-build}=1.0.27 conary-policy --resolve
if [ $? -ne 0 ]; then
    echo "WARNING: Conary not updated, you'll have to do this again manually."
    echo "Current version of conary is $(conary --version)"
    exit 1
fi

# backup the configuration files, as Conary may not keep them around
echo "Backing up configuration files to $BACKUPDIR"
[ ! -d $BACKUPDIR ] && mkdir $BACKUPDIR
cp ${RBUILDER_ROOT}/*.conf ${BACKUPDIR}

# update using conary 
# use conary migrate to break branch affinity and start fresh
echo "Migrating to group-rbuilder-dist=$INSTALL_LABEL_PATH"
yes | conary migrate group-rbuilder-dist=$INSTALL_LABEL_PATH --interactive --resolve
if [ $? -ne 0 ]; then
    echo "Problems occurred when updating rBuilder via Conary; exiting"
    exit 1
fi

# Move the old saved config, updating visibleImageTypes -> visibleBuildTypes
# along the way
echo "Restoring /srv/rbuilder/rbuilder.conf with updates"
sed -e 's/visibleImageTypes/visibleBuildTypes/g' $BACKUPDIR/rbuilder.conf > ${RBUILDER_ROOT}/rbuilder.conf

# Send a USR1 to httpd for good measure
killall -USR1 httpd > /dev/null 2>&1

echo "rBuilder 2.0.0 Migration complete."
exit 0
