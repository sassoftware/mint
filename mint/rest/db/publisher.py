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
