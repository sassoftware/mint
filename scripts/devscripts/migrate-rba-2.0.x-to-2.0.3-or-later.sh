#!/bin/sh
#
# Migration script used to migrate an rBuilder Appliance from 
# version 2.0.0 - 2.0.2 to version 2.0.3 or later

# Full install label to builds repository
INSTALL_LABEL_PATH="products.rpath.com@rpath:rba-2"
NEEDED_TROVES_AND_LABELS="group-rbuilder-dist=products.rpath.com@rpath:rba-1.6 group-rbuilder-dist=products.rpath.com@rpath:rba-2 conary=products.rpath.com@rpath:conary-1.1 raaplugins=products.rpath.com@rpath:raa-1-beta raaplugins=products.rpath.com@rpath:raa-1"

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
    2.0.[012])
        echo "Found version ${curr_ver} of group-rbuilder-dist."
        ;;
    2.0.[3456789])
        echo "Migration has already taken place. Exiting."
        exit 1
        ;;
    *)
        echo "Migration script will only migrate version 2.0.x to version 2.0.3 or later."
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

access_fail=1
for tl in $NEEDED_TROVES_AND_LABELS; do
    echo -n "Checking access to $tl... "
    conary rq $tl >& /dev/null
    if [ $? -ne 0 ]; then
        echo "failed"
        access_fail=0
    else
        echo "passed"
    fi
done

if [ $access_fail -eq 0 ]; then
    echo ""
    echo "It appears that your appliance cannot access this product update."
    echo "Contact a rPath sales engineer for assistance."
    exit 1
else
    echo "Access confirmed to product update. Migration proceeding."
    echo ""
fi

# start the migration here ####################################################

# backup the configuration files, as Conary will not keep them around
echo "Backing up configuration files to $BACKUPDIR"
[ ! -d $BACKUPDIR ] && mkdir $BACKUPDIR
cp ${RBUILDER_ROOT}/rbuilder.conf ${BACKUPDIR}

# update using conary
# use conary migrate to break branch affinity and start fresh
echo "Migrating to group-rbuilder-dist=$INSTALL_LABEL_PATH"
yes | conary migrate group-rbuilder-dist=$INSTALL_LABEL_PATH --interactive --resolve
if [ $? -ne 0 ]; then
    echo "Problems occurred when updating rBuilder via Conary; exiting"
    exit 1
fi

# split out configuration file
echo "Splitting rbuilder.conf into generated and custom pieces..."
python - <<EOSCRIPT
from mint import config

# these are keys that are generated for the "generated" configuration file
keysForGeneratedConfig = [ 'configured', 'hostName', 'siteDomainName',
                           'companyName', 'corpSite', 'defaultBranch',
                           'projectDomainName', 'externalDomainName', 'SSL',
                           'secureHost', 'bugsEmail', 'adminMail',
                           'externalPasswordURL', 'authCacheTimeout' ]

oldCfg = config.MintConfig()
oldCfg.read("${BACKUPDIR}/rbuilder.conf")

newCfg = config.MintConfig()
newCfg.read("${RBUILDER_ROOT}/rbuilder.conf")

allKeys = set(oldCfg.keys())
generatedKeys = set(keysForGeneratedConfig)
customKeys = allKeys - generatedKeys

# save "generated" keys to rbuilder-generated.conf
generatedFile = open("${RBUILDER_ROOT}/config/rbuilder-generated.conf", "w")
for k in generatedKeys:
    oldCfg.displayKey(k, out = generatedFile)
generatedFile.close()

# everything else that is different from the stock config goes
# in rbuilder-custom.conf
customFile = open("${RBUILDER_ROOT}/config/rbuilder-custom.conf", "w")
for k in customKeys:
    if newCfg[k] != oldCfg[k]:
        oldCfg.displayKey(k, out = customFile)
customFile.close()
EOSCRIPT

# Send a USR1 to httpd for good measure
killall -USR1 httpd > /dev/null 2>&1

echo "rBuilder 2.0.3 Migration complete."
exit 0
