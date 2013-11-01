$admin_email = 'admin@example.com'


class { 'appengine':
    # hostname => 'www.example.com',
    admin_email => $admin_email,
    namespace => 'sas',
    project_domain => 'sas-app-engine',
}


mailalias { 'root':
    recipient => $admin_email,
    ensure => present,
}
