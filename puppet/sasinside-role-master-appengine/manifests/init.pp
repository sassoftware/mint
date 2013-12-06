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

}
