#!/bin/sh
#
# Assumes conary is checked out in ../conary
# Assumes raa is checked out in ../raa
# Assumes raa is checked out in ../raa-test

rm -f .coverage

if [ -z "$CONARY_PATH" ]
then
    CONARY_PATH=../../../conary
fi

if [ -z "$CONARY_TEST_PATH" ]
then
    CONARY_TEST_PATH=../../../conary-test
fi

if [ -z "$RAA_PATH" ]
then
    RAA_PATH=../../../raa-2.1
fi

if [ -z "$RAA_TEST_PATH" ]
then
    RAA_TEST_PATH=../../../raa-test-2.1
fi

if [ -z "$MINT_PATH" ]
then
    MINT_PATH=../..
fi

if [ -z "$PLUGINS_PATH" ]
then
    PLUGINS_PATH=../../raaplugins
fi

if [ -z "$COVERAGE_PATH" ]
then
    COVERAGE_PATH=../../../utils
fi

export CONARY_PATH CONARY_TEST_PATH RAA_PATH RAA_TEST_PATH MINT_PATH COVERAGE_PATH
PYTHONPATH="$CONARY_PATH:$CONARY_TEST_PATH:$RAA_PATH:$RAA_TEST_PATH:$MINT_PATH:$PLUGINS_PATH:$COVERAGE_PATH:$PYTHONPATH" nosetests -v -p rPath "$@"
