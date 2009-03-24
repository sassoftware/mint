#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#


class EventPublisher(object):
    def __init__(self):
        self.subscribers = []

    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)
        
    def notify(self, event, *args, **kw):
        methodName = 'notify_' + event
        genericMethodName = 'notify'
        for subscriber in self.subscribers:
            method = getattr(subscriber, methodName, None)
            if method is not None:
                method(event, *args, **kw)
                continue
            method = getattr(subscriber, genericMethodName, None)
            if method is not None:
                method(event, *args, **kw)
                continue
