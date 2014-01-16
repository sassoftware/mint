class sasinside-role-master-appengine {
    firewall { '5000 accept HTTPS':
        proto  => 'tcp',
        dport  => '443',
        action => 'accept',
    }
    firewall { '5000 accept rMake RPC':
        proto  => 'tcp',
        dport  => '9999',
        action => 'accept',
    }
    firewall { '5000 accept rMake messagebus':
        proto  => 'tcp',
        dport  => '50900',
        action => 'accept',
    }
    firewall { '5000 accept rMake session':
        proto  => 'tcp',
        dport  => '63000-64000',
        action => 'accept',
    }

    include appengine

    rbuilder_user { 'admin':
        ensure              => present,
        full_name           => "Administrator",
        email               => "",
        is_admin            => true,
        default_password    => "password",
    }

    rbuilder_project { 'vdk':
        ensure                  => present,
        external                => true,
        display_name            => "SAS vApp Development Kit",
        repository_hostname     => "vdk.cny.sas.com",
        upstream_url            => $appengine::upstream_url,
    }

    rbuilder_platform { 'vapp.cny.sas.com@sas:vapp-2cw-devel':
        ensure                  => present,
        display_name            => "vApp 2cw CentOS Devel Workgroup Platform",
        upstream_url            => $appengine::upstream_url,
    }

    rbuilder_platform { 'vapp.cny.sas.com@sas:vapp-Mw-devel':
        ensure                  => present,
        display_name            => "vApp Mw CentOS Devel Workgroup Platform",
        upstream_url            => $appengine::upstream_url,
    }


}
