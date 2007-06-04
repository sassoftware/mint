#!/bin/sh
#
# Assumes conary is checked out in ../conary
# Assumes raa is checked out in ../raa
# Assumes raa is checked out in ../raa-test

rm -f .coverage

PYTHONPATH=../../../conary-test-1.1:../../:../../raaplugins/:../../../conary/:../../../raa-2.1/:../../../raa-test-2.1/:$PYTHONPATH nosetests -v -p rPath $@ 2>&1
