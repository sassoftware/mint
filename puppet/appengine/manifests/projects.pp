#
# Copyright (c) SAS Institute Inc.
#

class appengine::projects {

    rbuilder_project { 'pdt':
        ensure                  => present,
        external                => true,
        display_name            => "SAS Infrastructure",
        repository_hostname     => "pdt.cny.sas.com",
        upstream_url            => $sas_internal ? {
            true => "https://devrepos.unx.sas.com/conary/",
            default => "https://updates.sas.com/conary/",
            },
    }

    exec { '/usr/share/rbuilder/scripts/repository-sync': }

    Rbuilder_project <| |> -> Exec['/usr/share/rbuilder/scripts/repository-sync']

}
