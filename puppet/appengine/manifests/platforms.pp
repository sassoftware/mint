#
# Copyright (c) SAS Institute Inc.
#

class appengine::platforms {

    rbuilder_platform { 'rhel.rpath.com@rpath:rhel-6-server':
        ensure                  => present,
        display_name            => 'Red Hat Enterprise Linux 6',
        upstream_url            => $appengine::upstream_url,
    }

    rbuilder_platform { 'centos6.rpath.com@rpath:centos-6e':
        ensure                  => present,
        display_name            => 'CentOS 6',
        upstream_url            => $appengine::upstream_url,
    }

    #rbuilder_platform { 'windows.rpath.com@rpath:windows-common':
    #    ensure                  => present,
    #    display_name            => 'Windows Foundation Platform',
    #    upstream_url            => $appengine::upstream_url,
    #    abstract                => true,
    #}

}
