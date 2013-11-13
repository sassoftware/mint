require 'pathname'
require Pathname.new(__FILE__).dirname.dirname.expand_path + 'rbuilder'

Puppet::Type.type(:rbuilder_rmakeuser).provide(:api, :parent => Puppet::Provider::Rbuilder) do

    def exists?
        ok = admin ['rmakeuser-check']
        ok[0]
    end

    def create
        admin ['rmakeuser-create']
    end

end
