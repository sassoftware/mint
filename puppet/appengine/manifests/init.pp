#
# Copyright (c) SAS Institute Inc.
#


class appengine (
    $hostname                       = 'UNSET',
    $admin_email                    = 'UNSET',
    $project_domain                 = 'UNSET',
    $namespace                      = 'sas',
    $sentry_dsn                     = 'UNSET',
    ) {

    $site_fqdn = $hostname ? {
        'UNSET' => $fqdn,
        default => $hostname,
    }

    $email = $admin_email ? {
        'UNSET' => '',
        default => "
adminMail $admin_email
bugsEmail $admin_email
",
    }

    $_sentry_dsn = $sentry_dsn ? {
        'UNSET' => '',
        default => "sentryDSN $sentry_dsn",
    }

    $host_part   = regsubst($site_fqdn, '^([^.]+)[.](.*)$', '\1')
    $domain_part = regsubst($site_fqdn, '^([^.]+)[.](.*)$', '\2')

    file { '/srv/rbuilder/config/config.d/00_site.conf':
        ensure => file,
        content => "
configured True
hostName            $host_part
siteDomainName      $domain_part
secureHost          $site_fqdn
namespace           $namespace
projectDomainName   $project_domain
$email
$_sentry_dsn
",
        notify => Service['gunicorn'],
    }

    include appengine::rmake

    service { 'gunicorn':               ensure => running, enable => true }
    service { 'rbuilder-credstore':     ensure => running, enable => true }
    service { 'postgresql-rbuilder':    ensure => running, enable => true }
    service { 'pgbouncer':              ensure => running, enable => true, require => Service['postgresql-rbuilder'] }
    service { 'mcp-dispatcher':         ensure => running, enable => true, require => Service['rmake-messagebus'] }
    service { 'jobmaster':              ensure => running, enable => true, require => Service['rmake-messagebus'] }
    service { 'jabberd':                ensure => running, enable => true }
    service { 'rmake3':                 ensure => running, enable => true, require => Service['jabberd'] }
    service { 'rmake3-node':            ensure => running, enable => true, require => Service['jabberd'] }
}
