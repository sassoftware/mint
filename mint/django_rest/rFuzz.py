import random
from django.db import models
import inspect


def fuzzIt(module):
    for model in module.__dict__.values():
        if inspect.isclass(model):
            try:
                Fuzzer(model)
                print 'Success: %s' % model.__name__
                print '\n'
            except Exception, e:
                print 'Could not fuzz data %s' % model.__name__
                print e
    
    print '\n'
            
    for model in Fuzzer.REGISTRY:
        try:
            if not model.Meta.abstract:
                model.save()
                print 'Saved: %s' % model.__name__
            else:
                print 'Model was abstract, skipping save'
        except Exception, e:
            print 'Could not save data: %s' % model.__name__ 
            print e


class Fuzzer(object):
    
    integers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    strings = ['abc', 'def', 'ghi', 'jkl', 'mno', 'pqr', 'stu']
    words = ['the', 'crazy', 'bird', 'walks', 'off', 'pier']
    
    REGISTRY = set()
    
    def __init__(self, model, skip_fields=None):
        self.skip_fields = skip_fields if skip_fields else []
        self.m = model()
        if self.m not in Fuzzer.REGISTRY:
            self.fields = dict((f.name, f) for f in model._meta.fields)
            for fname, field in self.fields.items():
                if isinstance(field, models.ForeignKey):
                    if id(field.rel.get_related_field()) in [id(sf) for sf in self.skip_fields]:
                        continue
                elif isinstance(field, models.AutoField):
                    continue
                elif self.m.Meta.abstract:
                    continue
                data = self.dataFuzzer(field)
                import pdb; pdb.set_trace()
                setattr(self.m, fname, data)
            Fuzzer.REGISTRY.add(self.m)
        
    def dataFuzzer(self, field):
        if isinstance(field, models.CharField):
            return self.fuzzCharField()
        elif isinstance(field, models.IntegerField):
            return self.fuzzIntegerField()
        elif isinstance(field, models.TextField):
            return self.fuzzTextField()
        elif isinstance(field, models.BooleanField):
            return self.fuzzBooleanField()
        elif isinstance(field, models.ForeignKey):
            return self.fuzzForeignKeyField(field)
        elif isinstance(field, models.ManyToManyField):
            return self.fuzzManyToManyField()
        else:
            pass

    def fuzzCharField(self):
        return random.choice(Fuzzer.words)
        
    def fuzzIntegerField(self):
        return random.choice(Fuzzer.integers)
        
    def fuzzTextField(self):
        return random.choice(Fuzzer.words)
        
    def fuzzBooleanField(self):
        return random.choice([True, False])
        
    def fuzzForeignKeyField(self, field):
        related = field.related.model
        skipped = field.rel.get_related_field()
        return Fuzzer(related, skip_fields=[skipped,]).m
        
    def fuzzManyToManyField(self, field):
        import pdb; pdb.set_trace()
        pass