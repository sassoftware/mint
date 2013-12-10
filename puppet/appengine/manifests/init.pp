#
# Copyright (c) SAS Institute Inc.
#


class appengine (
    $hostname                       = 'UNSET',
    $admin_email                    = '',
    $project_domain                 = 'sas.app.engine',
    $namespace                      = 'sas',
    $sentry_dsn                     = 'UNSET',
    $upstream_url                   = hiera('sas.repos.url', 'https://updates.sas.com/conary/'),
    $site_entitlement               = hiera('sas.repos.entitlement', 'UNSET'),
    $site_proxy                     = hiera('sas.repos.proxy', 'UNSET'),
    ) {

    $banner = "# Managed by appengine puppet module, do not edit"

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

    $_site_entitlement = $site_entitlement ? {
        'UNSET' => '',
        default => "entitlement * $site_entitlement",
    }
    $_site_proxy = $site_proxy ? {
        'UNSET' => '',
        default => "\
proxy http $site_proxy
proxy https $site_proxy
",
    }

    file { '/srv/rbuilder/config/config.d/00_site.conf':
        ensure => file,
        content => "$banner
configured          True
hostName            $host_part
siteDomainName      $domain_part
secureHost          $site_fqdn
namespace           $namespace
projectDomainName   $project_domain
$email
$_sentry_dsn
$_site_entitlement
$_site_proxy
",
        notify => Service['gunicorn'],
    }

    file { '/etc/conary/config.d/50_site.conf':
        ensure => file,
        content => "$banner
$_site_entitlement
",
    }

    include appengine::rmake
    include appengine::projects
    include appengine::platforms

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
