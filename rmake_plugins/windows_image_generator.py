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

from mint.image_gen.wig import coordinator
from mint.image_gen.wig import handler as wig_handler
from mint.image_gen.wig import task as wig_task


class Plugin(plug_dispatcher.DispatcherPlugin, plug_worker.WorkerPlugin):

    handlerClasses = (wig_handler.WigHandler,)
    taskClasses = (wig_task.WigTask,)

    def dispatcher_pre_setup(self, dispatcher):
        super(Plugin, self).dispatcher_pre_setup(dispatcher)
        coordinator.start(dispatcher)
