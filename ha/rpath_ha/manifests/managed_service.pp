define rpath_ha::managed_service ($service=$title) {
    cs_primitive { $title:
        cib                         => $rpath_ha::cib,
        primitive_class             => 'lsb',
        primitive_type              => $service,
        parameters                  => {},
        operations                  => {},
    }

    service { $service:
        enable                      => false,
    }
}
