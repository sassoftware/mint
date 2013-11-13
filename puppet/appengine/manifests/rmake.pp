#
# Copyright (c) SAS Institute Inc.
#

class appengine::rmake {

    service { 'rmake-messagebus':       ensure => running, enable => true }
    service { 'rmake':                  ensure => running, enable => true, require => Service['rmake-messagebus'], notify => Service['rmake-node'] }
    service { 'rmake-node':             ensure => running, enable => true, require => Service['rmake'] }

    rbuilder_project { 'rmake-repository':
        ensure => present,
        hidden => true,
        display_name => "rMake Repository",
        description => "Please consider the contents of this product's repository to be for REFERENCE PURPOSES ONLY.\nThis product's repository is used by the rMake server running on this rBuilder for building packages and groups with Package Creator and Appliance Creator. This product is for the internal use of the rBuilder server. Do not attempt to manipulate the contents of this repository. Do not shadow, clone or otherwise reference any packages or components from this repository. This product can be reset at any time, which would lead to errors in anything that references the contents of this product's repository.",
        notify => Rbuilder_rmakeuser['rmake'],
    }

    rbuilder_rmakeuser { 'rmake':
        notify => Service['rmake'],
        ensure => present,
    }
}
