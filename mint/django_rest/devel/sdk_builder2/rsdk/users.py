from rsdk.Fields import *  # pyflakes=ignore
from rsdk.sdk import SDKModel, register, DynamicImportResolver  # pyflakes=ignore
from xobj2.xobj2 import XObj, XObjMetadata, Field  # pyflakes=ignore

REGISTRY = {}

@register
class UserGroup(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'user_group',
        elements = [
            Field('user_group_id', AutoField),
            Field('user_group', CharField)
        ],
        attributes = dict(
    
        ),
    )

@register
class User(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'user',
        elements = [
            Field('user_id', AutoField),
            Field('display_email', TextField),
            Field('passwd', CharField),
            Field('salt', TextField),
            Field('time_accessed', DecimalField),
            Field('time_created', DecimalField),
            Field('full_name', CharField),
            Field('active', SmallIntegerField),
            Field('user_name', CharField),
            Field('email', CharField),
            Field('blurb', TextField)
        ],
        attributes = dict(
    
        ),
    )

@register
class UserGroups(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'user_groups',
        elements = [
            Field('UserGroups', [UserGroup])
        ],
        attributes = dict(
            count=int,
            next_page=str,
            num_pages=str,
            previous_page=str,
            full_collection=str,
            filter_by=str,
            limit=str,
            order_by=str,
            per_page=str,
            end_index=str,
            start_index=str
        ),
    )

@register
class Users(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'users',
        elements = [
            Field('Users', [User])
        ],
        attributes = dict(
            count=int,
            next_page=str,
            num_pages=str,
            previous_page=str,
            full_collection=str,
            filter_by=str,
            limit=str,
            order_by=str,
            per_page=str,
            end_index=str,
            start_index=str
        ),
    )

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()

