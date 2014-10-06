#
# Copyright (c) SAS Institute Inc.
#

class appengine::projects {

    rbuilder_project { 'pdt':
        ensure                  => present,
        external                => true,
        display_name            => "SAS Infrastructure",
        repository_hostname     => "pdt.cny.sas.com",
        upstream_url            => $appengine::upstream_url,
    }

    rbuilder_project { 'vdk':
        ensure                  => present,
        external                => true,
        display_name            => "SAS vApp Development Kit",
        repository_hostname     => "vdk.cny.sas.com",
        upstream_url            => $appengine::upstream_url,
    }

    exec { '/usr/share/rbuilder/scripts/repository-sync': }

    Rbuilder_project <| |> -> Exec['/usr/share/rbuilder/scripts/repository-sync']

}
