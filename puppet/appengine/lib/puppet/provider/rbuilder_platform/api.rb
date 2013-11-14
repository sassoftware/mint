require 'pathname'
require Pathname.new(__FILE__).dirname.dirname.expand_path + 'rbuilder'

Puppet::Type.type(:rbuilder_platform).provide(:api, :parent => Puppet::Provider::Rbuilder) do

    def self.prefetch(resources)
        instances.each do |prov|
            if res = resources[prov.get('label')]
                res.provider = prov
            end
        end
    end

    def self.instances
        platforms = admin ['platform-list']
        platforms.map {|p| new({
            :ensure                 => p['enabled'] ? :present : :absent,
            :label                  => p['label'],
            :display_name           => p['platform_name'],
            :abstract               => p['abstract'],
            :upstream_url           => p['upstream_url'],
            })}
    end

    def exists?
        !(@property_hash[:ensure] == :absent or @property_hash.empty?)
    end

    def create
        admin(['platform-add',
                 '--label', resource[:label],
                 '--platform-name', resource[:display_name],
                 '--upstream-url', resource[:upstream_url],
                 '--enabled',
                 resource[:abstract] == :true ? '--abstract' : '',
                  ])
    end

end
