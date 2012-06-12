#
# Copyright (c) 2010 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

from rmake3.core import plug_dispatcher
from rmake3.worker import plug_worker

from mint.rmake3_package_creator import handler as rmake_handler
from mint.rmake3_package_creator import task as rmake_task

class PluginDownloadFiles(plug_dispatcher.DispatcherPlugin, plug_worker.WorkerPlugin):

    handlerClasses = (rmake_handler.HandlerDownloadFiles,)
    taskClasses = (rmake_task.TaskDownloadFiles,)

