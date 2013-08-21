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


class rpath_ha::drbd (
    $notify_email           = 'root',
    $nodes                  = 'UNSET',
    $mount                  = 'UNSET',
    $protocol               = 'C',
    $resource               = 'r1',
    $drbd_dev               = '/dev/drbd1',
    $cib                    = 'rpath_cib',
    ) {

    package { 'drbd':
        ensure              => present,
    }

    file { '/etc/drbd.d':
        ensure              => directory,
        recurse             => true,
        purge               => true,
    }

    file { '/etc/drbd.d/global_common.conf':
        ensure              => file,
        content             => template("${module_name}/drbd.conf.erb"),
    }

    file { "/etc/drbd.d/${resource}.res":
        ensure              => file,
        content             => template("${module_name}/drbd.res.erb"),
    }

    service { 'drbd':
        enable              => false,
        require             => Package['drbd'],
    }

    cs_primitive {
        'rpath_drbd':
        cib                         => $cib,
        primitive_class             => 'ocf',
        provided_by                 => 'linbit',
        primitive_type              => 'drbd',
        promotable                  => true,
        parameters => {
            'drbd_resource'         => $resource,
        },
        ms_metadata => {
            'notify'                => 'true',
            'clone-max'             => '2',
            'clone-node-max'        => '1',
        },
        operations => {
            # Operations in pacemaker are uniqued on name + interval, so the
            # interval must be different when two ops have the same name, even when
            # the role is different.
            'monitor-29s' => {
                'name'              => 'monitor',
                'interval'          => '29s',
                'role'              => 'Master',
            },
            'monitor-31s' => {
                'name'              => 'monitor',
                'interval'          => '31s',
                'role'              => 'Slave',
            },
            'start' => {
                'timeout'           => '240',
                'interval'          => '0',
            },
            'stop' => {
                'timeout'           => '100',
                'interval'          => '0',
            },
        },
    }

    cs_primitive {
        'rpath_fs':
        cib                         => $cib,
        primitive_class             => 'ocf',
        provided_by                 => 'heartbeat',
        primitive_type              => 'Filesystem',
        parameters => {
            'device'                => $drbd_dev,
            'directory'             => $mount,
            'fstype'                => 'ext4',
        },
        operations => {
            'start' => {
                'timeout'           => '240',
                'interval'          => '0',
            },
            'stop' => {
                'timeout'           => '100',
                'interval'          => '0',
            },
        },
    }

}
