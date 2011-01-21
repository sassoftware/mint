#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#


from rmake3.core import plug_dispatcher
from rmake3.worker import plug_worker

from rpath_repeater import launch


class LaunchPlugin(plug_dispatcher.DispatcherPlugin, plug_worker.WorkerPlugin):

    handlerClasses = (launch.LaunchHandler,)
    taskClasses = (launch.WaitForNetworkTask,)
