$admin_email = 'admin@example.com'


class { 'appengine':
    admin_email => $admin_email,
    namespace => 'sas',
    project_domain => 'app.engine',
    upstream_url => 'https://updates.sas.com/conary/',
    # hostname => 'www.example.com',
    # sentry_dsn => 'https://xxx:yyy@sentry.example.com/1234',
}

#rbuilder_project { 'example':
#    ensure                  => present,
#    external                => true,
#    display_name            => "Example External Project",
#    repository_hostname     => "conary.example.com",
#    upstream_url            => "https://conary.example.com/conary/",
#}


mailalias { 'root':
    recipient => $admin_email,
    ensure => present,
}
