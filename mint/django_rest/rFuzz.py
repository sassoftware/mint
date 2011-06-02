import random
from django.db import models
import inspect


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

    for fuzz in fuzzCollection:
        try:
            if not fuzz.Meta.abstract:
                fuzz.save()
                print 'Saved: %s' % fuzz
        except Exception, e:
            print 'Could not save data %s: %s' % (fuzz, e) 


class Fuzzer(object):

    integers = range(0, 1000)
    strings = ['abc', 'def', 'ghi', 'jkl', 'mno', 'pqr', 'stu']
    words = ['the', 'crazy', 'bird', 'walks', 'off', 'pier']
    
    FKREGISTRY = {}

    def __init__(self, model, skip=None):
        self.skipped = skip if skip else []
        self.m = model if isinstance(model, models.Model) else model()
        self.fields = dict((f.name, f) for f in model._meta.fields)
        for fname, field in self.fields.items():
            hsh = id(self.m)
            if isinstance(field, (models.ForeignKey, models.ManyToManyField)):
                if hsh in Fuzzer.FKREGISTRY:
                    continue
                else:
                    instance = self.fuzzForeignKeyField(field)
                    Fuzzer.FKREGISTRY[id(self.m)] = (self.m, field.name, instance)
                setattr(*Fuzzer.FKREGISTRY[hsh])
            else:
                data = self.fuzzData(field)
                setattr(self.m, fname, data)

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