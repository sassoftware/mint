cs_primitive { '@name@':
    cib                         => 'rpath_cib',
    primitive_class             => 'lsb',
    primitive_type              => '@name@',
    parameters                  => {},
    operations                  => {},
}

service { '@name@':
    enable                      => false,
}


