require 'pathname'
require Pathname.new(__FILE__).dirname.dirname.expand_path + 'rbuilder'

Puppet::Type.type(:rbuilder_project).provide(:api, :parent => Puppet::Provider::Rbuilder) do

    def self.prefetch(resources)
        instances.each do |prov|
            if res = resources[prov.name.to_s]
                res.provider = prov
            end
        end
    end

    def self.instances
        projects = admin ['project-list']
        projects.map {|project| new({
            :ensure                 => :present,
            :name                   => project['short_name'],
            :display_name           => project['name'],
            :repository_hostname    => project['repository_hostname'],
            :description            => project['description'],
            :hidden                 => project['hidden'],
            :external               => project['external'],
            :upstream_url           => project['upstream_url'],
            })}
    end

    def exists?
        !(@property_hash[:ensure] == :absent or @property_hash.empty?)
    end

    def create
        admin(['project-add',
                 '--short-name', resource[:name],
                 '--name', resource[:display_name],
                 '--description', resource[:description],
                 '--repository-hostname', resource[:repository_hostname],
                 '--upstream-url', resource[:upstream_url],
                 resource[:hidden] == :true ? '--hidden' : '',
                 resource[:external] == :true ? '--external' : '',
                  ])
    end

    def destroy
        Puppet::Util::Execution.execute [
            '/usr/share/rbuilder/scripts/deleteproject',
            '--force', resource[:name],
            ]
    end

end
