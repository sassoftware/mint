require 'pathname'
require Pathname.new(__FILE__).dirname.dirname.expand_path + 'rbuilder'

Puppet::Type.type(:rbuilder_user).provide(:api, :parent => Puppet::Provider::Rbuilder) do

    def self.prefetch(resources)
        instances.each do |prov|
            if res = resources[prov.name.to_s]
                res.provider = prov
            end
        end
    end

    def self.instances
        users = admin ['user-list']
        users.map {|user| new({
            :ensure                 => :present,
            :name                   => user['user_name'],
            :full_name              => user['full_name'],
            :email                  => user['email'],
            :is_admin               => user['is_admin'],
            })}
    end

    def exists?
        !(@property_hash[:ensure] == :absent or @property_hash.empty?)
    end

    def create
        admin(['user-add',
                 '--user-name', resource[:name],
                 '--full-name', resource[:full_name],
                 '--email', resource[:email],
                 '--admin', (resource[:is_admin] == :true ? 'yes' : 'no'),
                 '--password', resource[:default_password],
                  ])
    end

end
