#
# Copyright (c) 2008 rPath, Inc
# All rights reserved
#

from gettext import gettext as _

from raa import authorization
from raa import web
from raa.modules import raawebplugin
from rPath import rmakemanagement

class rMakeManagement(raawebplugin.rAAWebPlugin):
    """
    Plugin for managing a rMake server and one or many rMake nodes.  

    Allows:
    1. start/stop/restart/reset of both server and nodes.  
    2. configuration of server and nodes.
    3. log viewing of rmake builds
    """

    displayName = _("rMake Management")
    tooltip = _("Manage and configure rMake server and nodes")
    services_plugin = '/services/Services'


    @web.expose(allow_xmlrpc=True, template="rPath.rmakemanagement.index")
    def index(self):
        builds = self._getBuilds()
        status = self._getServiceStatus(rmakemanagement.rMakeServiceName)
        # Get the hostname of this system since we're going against the local
        # rmake
        netinfo = self.plugins['/configure/Network'].index()
        self.host = netinfo.get('host_hostName', _('Local rMake server'))
        nodes = self._getNodes()

        
        return dict(server=self.host,
                    status=status,
                    builds=builds,
                    nodes=nodes
                    )


    def _getBuilds(self):
        """
        Return a list of builds stored on the rMake server, up to the
        configured limit.
        """
        limit = web.getConfigValue('rmake.build_display_limit', 5)
        builds = self.callBackend('getBuilds', limit)

        # We want the most recent builds at the top
        builds.sort()
        builds.reverse()
        return builds


    def _getNodes(self):
        """
        Return a list of attached nodes to the local rMake server.
        """
        nodes = self.callBackend('getNodes')
        node_dict = {}

        for node in nodes:
            node_dict[self.host] = {}
            node_dict[self.host]['status'] = node[0]
            node_dict[self.host]['slots'] = node[1]
            node_dict[self.host]['chrootLimit'] = node[2]
        return node_dict


    @web.expose(allow_xmlrpc=True)
    def editNode(self, node, slots, chrootLimit):
        self.callBackend('editNode', node, slots, chrootLimit)
        return True


    @web.expose(allow_xmlrpc=True, allow_json=True)
    def getBuildLog(self, buildId):
        """
        Return the log for a build.
        """
        # Make sure we were passed an int
        buildId = int(buildId)
        build_log = self.callBackend('getBuildLog', buildId)
        return dict(logText=build_log)


    @web.expose(allow_xmlrpc=True)
    @web.require(authorization.LocalhostOnly())
    def getConfigData(self):
        """
        Returns the config data for the rMake plugin.
        """

        # TODO
        # Ideally we need a method in raa.web to return a config section.
        config = {}

        config['rmake.build_display_limit'] = \
            web.getConfigValue('rmake.build_display_limit',
                               path=rmakemanagement.pluginpath)
        config['rmake.db'] = \
            web.getConfigValue('rmake.db',
                               path=rmakemanagement.pluginpath)
        config['rmake.contents'] = \
            web.getConfigValue('rmake.contents',
                               path=rmakemanagement.pluginpath)
        config['rmake.node_config_file'] = \
            web.getConfigValue('rmake.node_config_file', 
                               path=rmakemanagement.pluginpath)

        return config


    @web.expose(allow_xmlrpc=True, allow_json=True)
    @raawebplugin.immedTask
    def changeServerState(self, service, action):
        """
        Change the state of a service.
        @type srv: string
        @param srv: Name of the service.
        @type act: integer enum
        @param act: The action to take.
        @rtype: dictionary
        @return: mapping containing the success message or errors.
        """
        
        def callback(schedId):
            """
            A method to save the schedId, which is used as a reference back
            to the exact action we're performing.
            """
            service_plugin = self.plugins[self.services_plugin]
            service_table = service_plugin.getattr('servicesTable')
            service_table.saveJob(schedId, service, action)

        return dict(callback=callback)
    

    def _getServiceStatus(self, service_name):
        status = self.callBackend('getServiceStatus', service_name)
        return status
        # return rmakemanagement.status.toString[status]
 

    @web.expose(allow_xmlrpc=True)
    @web.require(authorization.LocalhostOnly())
    def getJobProp(self, schedId):
        """
        Get information about the job to perform.
        @param schedId: ID of the job to perform.
        """
        service_plugin = self.plugins[self.services_plugin]
        service_table = service_plugin.getattr('servicesTable')
        return service_table.getJobProp(schedId)


    @web.expose(allow_xmlrpc=True, template="rPath.rmakemanagement.nodes")
    def nodes(self):
        return {}

