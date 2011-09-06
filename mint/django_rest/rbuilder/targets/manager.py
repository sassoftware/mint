from mint.django_rest.rbuilder import auth
from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.targets import models

class TargetsManager(basemanager.BaseManager):
    @exposed
    def getTargetById(self, target_id):
        return models.Target.objects.get(pk=target_id)
        
    @exposed
    def getTargets(self):
        Targets = models.Targets()
        Targets.target = models.Target.objects.all()
        return Targets
        
    @exposed
    def createTarget(self, target):
        target.save()
        return target
        
    @exposed
    def updateTarget(self, target_id, target):
        target.save()
        return target
        
    @exposed
    def deleteTarget(self, target_id):
        target = models.Target.objects.get(pk=target_id)
        target.delete()
        
        
class TargetTypesManager(basemanager.BaseManager):
    @exposed
    def getTargetTypeById(self, target_type_id):
        return models.TargetType.objects.get(pk=target_type_id)
        
    @exposed
    def getTargetTypes(self):
        TargetTypes = models.TargetTypes()
        TargetTypes.target_type = models.TargetType.objects.all()
        return TargetTypes
        
        
class TargetCredentialsManager(basemanager.BaseManager):
    @exposed
    def getTargetCredentialsForTargetByUserId(self, target_id, user_id):
        return models.TargetUserCredentials.objects.filter(target_id=target_id, user_id=user_id)