#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

require 'puppet/provider/package'

Puppet::Type.type(:package).provide :conary, :parent => Puppet::Provider::Package do
  has_feature :versionable

  commands :conary => "conary"

  def self.parse(line)
    if line.chomp =~ /^([^=]+)=([^\[]+)\/([^\/\[]+)(?:\[.*)?$/
      {:ensure => $2, :name => $1, :provider => name}
    else
      nil
    end
  end

  if command('conary')
    confine :true => begin
      conary('--version')
      rescue Puppet::ExecutionFailure
        false
      else
        true
      end
  end

  def self.instances
    packages = []
    execpipe("#{command(:conary)} q --labels --config 'fullversions false'") { |process|
      process.each { |line|
        next unless options = parse(line)
        packages << new(options)
      }
    }
    packages
  end

  def query
    cmd = ["q", @resource[:name], "--labels", "--config", "fullversions false"]
    begin
      output = conary(*cmd)
    rescue Puppet::ExecutionFailure
      return nil
    end
    @property_hash.update(self.class.parse(output))
    @property_hash.dup
  end
end
