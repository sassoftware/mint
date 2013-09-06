define rpath_ha::order ($first, $then) {
    cs_colocation { "colo_${title}":
        cib                         => $rpath_ha::cib,
        primitives                  => [$first, $then],
    }
    cs_order { "order_${title}":
        cib                         => $rpath_ha::cib,
        first                       => $first,
        second                      => $then,
    }
}
