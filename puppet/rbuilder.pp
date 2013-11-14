$admin_email = 'admin@example.com'


class { 'appengine':
    admin_email => $admin_email,
    namespace => 'sas',
    project_domain => 'sas-app-engine',
    upstream_url => 'https://updates.sas.com/conary/',
    # hostname => 'www.example.com',
    # sentry_dsn => 'https://xxx:yyy@sentry.example.com/1234',
}


mailalias { 'root':
    recipient => $admin_email,
    ensure => present,
}
