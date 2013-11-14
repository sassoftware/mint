Puppet::Type.newtype(:rbuilder_project) do
    ensurable

    newparam(:name) do
      desc "Project unique name"
      isnamevar
    end

    newparam(:display_name) do
      desc "Project display name"
    end

    newparam(:repository_hostname) do
      desc "Optional repository FQDN"
    end

    newparam(:description) do
      desc "Optional description for the project"
    end

    newparam(:hidden) do
      desc "If true, the project requires authentication to read"
      newvalues(:true, :false)
      defaultto false
    end

    newparam(:external) do
      desc "If true, the project is external"
      newvalues(:true, :false)
      defaultto false
    end

    newparam(:upstream_url) do
      desc "URL of the upstream repository if external"
    end

    autorequire(:service) do
      [ 'gunicorn' ]
    end
end
