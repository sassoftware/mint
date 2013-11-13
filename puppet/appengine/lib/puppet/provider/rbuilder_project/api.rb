require 'pathname'
require Pathname.new(__FILE__).dirname.dirname.expand_path + 'rbuilder'

Puppet::Type.type(:rbuilder_project).provide(:api, :parent => Puppet::Provider::Rbuilder) do

    def instances
        projects = admin ['project-list']
        instances = projects.map {|project| {
            :short_name           => project['short_name'],
            :display_name         => project['name'],
            :repository_hostname  => project['repository_hostname'],
            :description          => project['description'],
        }}
        instances
    end

    def exists?
        instances.any? {|project| project[:short_name] == resource[:short_name]}
    end

    def create
        admin(['project-add',
                 '--short-name', resource[:short_name],
                 '--name', resource[:display_name],
                 '--description', resource[:description],
                 '--repository-hostname', resource[:repository_hostname],
                 resource[:hidden] == :true ? '--hidden' : '',
                  ])
    end

    def destroy
        Puppet::Util::Execution.execute [
            '/usr/share/rbuilder/scripts/deleteproject',
            '--force', resource[:short_name],
            ]
    end

end
