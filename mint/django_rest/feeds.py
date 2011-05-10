#
# Copyright (c) 2011 rPath, Inc.
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



from django.contrib.syndication.views import Feed
from django.utils import feedgenerator
from mint.django_rest.rbuilder.notices.models import UserNotice, GlobalNotice

class NoticesFeed(Feed):
    feed_type = feedgenerator.Rss201rev2Feed

    def description(self, obj):
        return obj.description

    def item_title(self, obj):
        return obj.title
    
    def item_link(self, obj):
        return obj.link
        
    def get_object(self, request, *args, **kwargs):
        pass
        

class UserNoticesFeed(NoticesFeed):
    def items(self):
        return UserNotice.objects.all()
    
    
class GlobalNoticesFeed(NoticesFeed):
    def items(self):
        return GlobalNotice.objects.all()
    
    
    
    
    