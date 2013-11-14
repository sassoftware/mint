Puppet::Type.newtype(:rbuilder_platform) do
    ensurable

    newparam(:label) do
      desc "Platform label"
      isnamevar
    end

    newparam(:display_name) do
      desc "Platform display name"
    end

    newparam(:abstract) do
      newvalues(:true, :false)
      defaultto false
    end

    newparam(:upstream_url) do
      desc "URL of the upstream repository for this platform"
    end

    autorequire(:service) do
      [ 'gunicorn' ]
    end
end
