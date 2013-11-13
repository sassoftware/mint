Puppet::Type.newtype(:rbuilder_rmakeuser) do
    ensurable

    newparam(:name) do
      desc "Name (ignored)"
      isnamevar
    end

    autorequire(:service) do
        [ 'gunicorn' ]
    end

    autorequire(:rbuilder_project) do
        [ 'rmake-repository' ]
    end
end
