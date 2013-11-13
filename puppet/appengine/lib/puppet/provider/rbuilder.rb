#
# Copyright (c) SAS Institute Inc.
#

require 'json'


class Puppet::Provider::Rbuilder < Puppet::Provider
  initvars
  commands :mint_admin => '/usr/share/rbuilder/scripts/mint-admin'

  def admin(args)
      cmd = [ command(:mint_admin), '--json' ] + args
      raw = Puppet::Util::Execution.execute(cmd, :failonfail => true)
      JSON.parse(raw)
  end
end
