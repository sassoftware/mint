cs_group { 'rpath':
    cib                         => 'rpath_cib',
    primitives => [
        'rpath_ip',
        'rpath_fs',
        @prims@
        ],
}
