class { 'rpath_ha':
    service_ip                  => '172.25.0.50',
    multicast_network           => '172.25.0.0',
    multicast_address           => '239.255.1.1',
    drbd_nodes => [
        {   name                => 'rbuilder-1.mydomain',
            address             => '172.25.0.101:7789',
            disk                => '/dev/sdb1',
            },
        {   name                => 'rbuilder-2.mydomain',
            address             => '172.25.0.102:7789',
            disk                => '/dev/sdb1',
            },
        ],
}

service { 'raa':        enable  => false }
service { 'iptables':   enable  => false }
service { 'ip6tables':  enable  => false }

Package { provider => "conary" }
