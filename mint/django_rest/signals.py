#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db.backends import signals
from django.dispatch import Signal

post_commit = Signal(providing_args=['connection'])

# Hook up the post-commit signal.
# We monkey-patch the connection's commit method.
def postCommitHandler(connection=None, **kwargs):
    if getattr(connection, '_with_post_commit_signal', None):
        return
    connection._with_post_commit_signal = True
    origCommit = connection._commit
    def commitWithSignal():
        ret = origCommit()
        post_commit.send(sender=connection.__class__, connection=connection)
        return ret
    connection._commit = commitWithSignal

signals.connection_created.connect(postCommitHandler)

class PostCommitActions(object):
    """
    Registry for actions that have to be executed post-commit.
    This is not job-specific, but jobs are the ones dealing with rmake3, and
    that is the primary use case:
        * create job resource
        * commit current transaction
        * create message bus job and execute it
    If we create the message bus job inside the current transaction, it is
    possible for it to finish before the job resource is committed.
    """
    actions = []

    @classmethod
    def postCommit(cls, connection=None, **kwargs):
        if not cls.actions:
            # Short-cut for the general case of no change
            return
        # Copy the list of actions to be executed, and clear the list,
        # just in case we try to use the connection again.
        currentActions = cls.actions
        cls.actions = []

        if connection.is_managed():
            if connection.is_dirty():
                connection.commit()
            connection.leave_transaction_management()
            connection.enter_transaction_management()
        try:
            for action in currentActions:
                action(connection=connection)
        except:
            if connection.is_dirty():
                connection.rollback()
            raise
        else:
            if connection.is_dirty():
                connection.commit()

    @classmethod
    def add(cls, action):
        cls.actions.append(action)

post_commit.connect(PostCommitActions.postCommit)
