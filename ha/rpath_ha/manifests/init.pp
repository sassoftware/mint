#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


class rpath_ha (
    $service_ip                     = 'UNSET',
    $multicast_network              = 'UNSET',
    $multicast_address              = 'UNSET',
    $drbd_nodes                     = 'UNSET',
    $mount_point                    = '/srv',
    ) {

    $cib = 'rpath_cib'

    class { 'corosync':
        enable_secauth              => false,
        bind_address                => $multicast_network,
        multicast_address           => $multicast_address,
        corosync_conf               => "${module_name}/corosync.conf.two_node.erb",
    }

    class { 'rpath_ha::drbd':
        protocol                    => 'C',
        mount                       => $mount_point,
        nodes                       => $drbd_nodes,
        cib                         => $cib,
    }

    # Manage pacemaker as a separate initscript. puppet-corosync normally wants
    # it to be managed by corosync, but that doesn't work for some reason.
    service { 'pacemaker':
        ensure                      => running,
        enable                      => true,
        require                     => Service['corosync'],
    }

    service { 'rbuilder':
        enable                      => false,
    }

    file { '/etc/rc.d/init.d/rbuilder-ha-cron':
        ensure                      => link,
        target                      => '/usr/share/rbuilder/ha/rbuilder-ha-cron',
    }
    File['/etc/rc.d/init.d/rbuilder-ha-cron'] -> Service['rbuilder-ha-cron']

    # Write changes to a shadow CIB so they can be committed all at once
    cs_shadow { $cib: }

    # stonith will not be used
    cs_property { 'stonith-enabled':   value => 'false' }
    # corosync is providing quorum in two-node mode, so do enable quorum here
    cs_property { 'no-quorum-policy':  value => 'stop' }

    # stonith must be disabled before any other crm calls are performed,
    # otherwise they hang waiting for stonith to start
    Cs_property['stonith-enabled'] -> Cs_primitive <| |>
    Cs_property['stonith-enabled'] -> Cs_shadow <| |>

    cs_primitive {
        'rpath_ip':
        cib                         => $cib,
        primitive_class             => 'ocf',
        provided_by                 => 'heartbeat',
        primitive_type              => 'IPaddr2',
        parameters => {
            'ip'                    => $service_ip,
            'cidr_netmask'          => '32',
        },
        operations => {
            'monitor'               => { 'interval' => '10s' },
        },
    }

    include rpath_ha::managed_services

    cs_group { 'rpath':
        cib                         => $cib,
        primitives => concat([
            'rpath_ip',
            'rpath_fs',
            ], $rpath_ha::managed_services::services),
    }

    # Services must reside on the same node as the block device on which they
    # run
    cs_colocation {
        'colocate_rpath':
        cib                         => $cib,
        primitives                  => ['rpath', 'ms_rpath_drbd:Master'],
        require                     => Cs_group['rpath']
    }

    # The service group starts after a DRBD master is promoted (started)
    cs_order {
        'order_rpath':
        cib                         => $cib,
        first                       => 'ms_rpath_drbd:promote',
        second                      => 'rpath:start',
        require                     => Cs_group['rpath']
    }
}
