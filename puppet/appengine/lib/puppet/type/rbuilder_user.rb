Puppet::Type.newtype(:rbuilder_user) do
    ensurable

    newparam(:name) do
      desc "Username"
      isnamevar
    end

    newparam(:full_name) do
      desc "User's full name"
    end

    newparam(:email) do
      desc "User's email"
    end

    newparam(:is_admin) do
      desc "If true, the user is an administrator"
      newvalues(:true, :false)
      defaultto false
    end

    newparam(:default_password) do
      desc "User's initial password"
    end

    autorequire(:service) do
      [ 'gunicorn' ]
    end
end
