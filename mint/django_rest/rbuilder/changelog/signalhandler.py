#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.db.models.signals import post_init
from django.db.models.signals import post_save
from django.db.models.signals import m2m_changed

from mint.django_rest.rbuilder.changelog import models as changelogmodels

def postInit(sender, instance, **kwargs):
    if hasattr(instance, '_saveFields'):
        instance._saveFields()

def postSave(sender, instance, **kwargs):
    if not hasattr(instance, '_saveFields'):
        return
    logChanges(instance)
    instance._saveFields()

def m2mChanged(sender, instance, **kwargs):
    action = kwargs['action']
    if action not in ['post_add', 'post_remove']:
        return

    tag = instance.getTag()
    m2mFields = [f[0] for f in instance._meta.get_m2m_with_model()]
    fieldName = None
    for m2mField in m2mFields:
        if m2mField.m2m_db_table() == sender._meta.db_table:
            fieldName = m2mField.name
            break
    if not fieldName or fieldName not in instance.logged_fields:
        return
    model = kwargs['model']
    modelInst = model.objects.get(pk=kwargs['pk_set'].pop())
    if action == 'post_add':
        entryText = "%s added to %s" % (modelInst, fieldName)
    if action == 'post_remove':
        entryText = "%s removed from %s" % (modelInst, fieldName)
    changeLog, created = changelogmodels.ChangeLog.objects.get_or_create(
        resource_type=tag, resource_id=instance.pk)
    changeLogEntry = changelogmodels.ChangeLogEntry(change_log=changeLog,
        entry_text=entryText)
    changeLog.save()
    changeLogEntry.save()

def logChanges(instance):
    changedFields = instance.getChangedFields()
    if not changedFields:
        return

    tag = instance.getTag()

    changeLog, created = changelogmodels.ChangeLog.objects.get_or_create(
        resource_type=tag, resource_id=instance.pk)
    for field, oldValue in changedFields.items():
        newValue = getattr(instance, field)
        if oldValue:
            entryText = "%s updated from %s to %s" % (field, oldValue, newValue)
        else:
            entryText = "%s set to %s" % (field, newValue)
        changeLogEntry = changelogmodels.ChangeLogEntry(change_log=changeLog,
            entry_text=entryText)
        changeLogEntry.save()

    changeLog.save()

post_init.connect(postInit)
post_save.connect(postSave)
m2m_changed.connect(m2mChanged)
