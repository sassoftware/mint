import random
from django.db import models
import inspect
from django.db.models.loading import cache

def findAllModels():
    d = {}
    for app in cache.get_apps():
        app_label = app.__name__.split('.')[-2]
        d[app_label] = app
    return d

def fuzzIt(module):
    fuzzCollection = []
    
    for model in module.__dict__.values():
        if inspect.isclass(model):
            try:
                if not model.Meta.abstract:
                    fuzzCollection.append(Fuzzer(model).m)
                print 'Success: %s' % model
            except Exception, e:
                print 'Could not fuzz data %s: %s' % (model, e)
    
    print '\n'
    print '\n'

    # for fuzz in fuzzCollection:
    #     try:
    #         if not fuzz.Meta.abstract:
    #             fuzz.save()
    #             print 'Saved: %s' % fuzz
    #         else:
    #             print 'Was abstract, not saving'
    #     except Exception, e:
    #         print 'Could not save data %s: %s' % (fuzz, e) 


class Fuzzer(object):

    integers = range(0, 1000)
    strings = ['abc', 'def', 'ghi', 'jkl', 'mno', 'pqr', 'stu']
    words = ['the', 'crazy', 'bird', 'walks', 'off', 'pier']
    
    FKREGISTRY = {}

    def __init__(self, model, skip=None, force=None):
        self.skipped = skip if skip else []
        self.forced = force if force else {}
        self.m = model if isinstance(model, models.Model) else model(pk=random.choice(Fuzzer.integers))
        self.fields = dict((f.name, f) for f in model._meta.fields)
        
        if hasattr(self.m, '_obscurred'):
            self.fields.update(
                dict((obscurred, getattr(self.m, obscurred)) for obscurred in self.m._obscurred))

        for fname, field in self.fields.items():
            hsh = id(self.m)
            if isinstance(field, models.ForeignKey):
                if hsh in Fuzzer.FKREGISTRY:
                    continue
                else:
                    instance = self.fuzzForeignKeyField(field)
                    Fuzzer.FKREGISTRY[hsh] = (self.m, field.name, instance)
                    setattr(*Fuzzer.FKREGISTRY[hsh])
            elif isinstance(field, models.Manager):
                if hasattr(field, 'through'):
                    through = field.through
                    through_fields = dict((f.name, f) for f in through._meta.fields)
                    related = {}

                    for tFname, tField in through_fields.items():
                        if hasattr(tField, 'rel'):
                            if hasattr(tField.rel, 'to'):
                                related[tFname] = tField.rel.to

                    data = {}

                    for rFname, rField in related.items():
                        if isinstance(self.m, rField):
                            data[rFname] = self.m
                        elif issubclass(field.model, rField):
                            data[rFname] = Fuzzer(field.model).m
                    field.through.objects.create(**data).save()
            else:
                data = self.fuzzData(field)
                setattr(self.m, fname, data)
        import pdb; pdb.set_trace()
        self.m.save()

    def fuzzData(self, field):
        if isinstance(field, models.AutoField):
            return self.fuzzAutoField()
        if isinstance(field, models.CharField):
            return self.fuzzCharField()
        elif isinstance(field, models.IntegerField):
            return self.fuzzIntegerField()
        elif isinstance(field, models.TextField):
            return self.fuzzTextField()
        elif isinstance(field, models.BooleanField):
            return self.fuzzBooleanField()
        elif isinstance(field, models.DecimalField):
            return self.fuzzDecimalField()
        else:
            import pdb; pdb.set_trace()

    def fuzzDecimalField(self):
        return random.choice(Fuzzer.integers)

    def fuzzAutoField(self):
        return random.choice(Fuzzer.integers)

    def fuzzCharField(self):
        return random.choice(Fuzzer.words)

    def fuzzIntegerField(self):
        return random.choice(Fuzzer.integers)

    def fuzzTextField(self):
        return random.choice(Fuzzer.words)

    def fuzzBooleanField(self):
        return random.choice([True, False])

    def fuzzForeignKeyField(self, field):
        related = field.related.parent_model
        return Fuzzer(related).m

    def fuzzManyToManyField(self, field):
        import pdb; pdb.set_trace()
        pass