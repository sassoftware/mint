import random
from django.db import models
import inspect
# from mint.django_rest.rbuilder.projects import models as pmodels
# from mint.django_rest.rbuilder.users import models as umodels

class ValidationError(Exception):
    pass

def fuzzIt(module):
    mdls = dict((m.__name__, m) for m in module.__dict__.values() if inspect.isclass(m))
    for mname, model in mdls.items():
        try:
            f = Fuzzer(model)
            f.fz.instance.save()
        except Exception, e:
            print "Couldn't fuzz model %s: %s" % (model, e)
        print 'Fuzzed %s' % model
    
    for instance in Fuzzer.MDLREGISTRY.values():
        try:
            instance.save()
        except Exception, e:
            print "Couldn't save instance %s: %s" % (instance, e)
        print 'Fuzzed %s' % instance

def toFuzz(mdl):
    pass

def validate(fuzz):
    passed = {}
    failed = {}
    for fname, field in fuzz.fields.items():
        # attr = {field.column:getattr(fuzz.instance, field.column)}
        attr = {field.column:getattr(fuzz.instance, fname)}
        try:
            qs = fuzz.instance.__class__.objects.filter(**attr)
            passed[fname] = (attr, qs)
        except:
            failed[fname] = (attr, field)
    return passed, failed


class FuzzyModel(object):
    def __init__(self, model, **kwargs):
        self.model = model.__class__ if isinstance(model, models.Model) else model
        # self.instance = model if isinstance(model, models.Model) else model()
        self.instance = self.get_or_create(**kwargs)
        self.fields = dict((f.name, f) for f in self.instance._meta.fields)
    
    def get_or_create(self, **kwargs):
        module = inspect.getmodule(self.model)
        mdlName = self.model.__name__
        try:
            qs_all = getattr(module, mdlName).objects.all()
            qs_filtered = qs_all.filter(**kwargs)
            instance = self.rand_instance_from_qs(qs_filtered)
        except Exception, e:
            instance = self.gen_instance(self.model)
        return instance

    def rand_instance_from_qs(self, qs):
        numResults = len(qs)
        if numResults:
            rng = range(0, numResults)
            return qs[random.choice(rng)]
        else:
            return self.gen_instance(self.model)
    
    def gen_instance(self, model):
        return model if isinstance(model, models.Model) else model()           

    def save(self):
        self.instance.save()
    
    @property
    def SimpleFields(self):
        fields = {}
        for fname, field in self.fields.items():
            if fname not in self.FKFields:
                fields[fname] = field
        return fields

    @property
    def FKFields(self):
        return dict((k, v) for k, v in self.fields.items() if isinstance(v, models.ForeignKey))

    @property
    def M2MFields(self):
        m2m_accessors = {}
        for m in self.instance._meta.get_m2m_with_model():
            f = m[0]
            try:
                m2m_accessors[f.name] = getattr(self.instance, f.name)
            except ValueError:
                pass
        return m2m_accessors


class Fuzzer(object):

    MDLREGISTRY = {}
    FKREGISTRY = {}
    M2MREGISTRY = {}

    integers = range(0, 1000)
    strings = ['abc', 'def', 'ghi', 'jkl', 'mno', 'pqr', 'stu']
    words = ['the', 'crazy', 'bird', 'walks', 'off', 'pier']

    def __init__(self, model, skip=None, force=None, fz_params=None):
        self.fz_params = fz_params if fz_params else {}
        self.fz = FuzzyModel(model, **self.fz_params)
        self.skipped = skip if skip else []
        self.forced = force if force else {}
        self.DONE = []

        Fuzzer.MDLREGISTRY[self.fz.model.__name__] = self.fz.instance

        for fname, field in self.fz.SimpleFields.items():
            if fname in self.forced:
                setattr(self.fz.instance, fname, self.forced[fname])
                continue
            if field in self.skipped:
                continue

            self.fuzzData(fname, field)
            self.DONE.append((fname, field))

        for fname, fk in self.fz.FKFields.items():
            if fname in self.forced:
                setattr(self.fz.instance, fname, self.forced[fname])
                continue
            if fk in self.skipped:
                continue

            self.fuzzFK(fname, fk)
            self.DONE.append((fname, fk))

        for fname, accessor in self.fz.M2MFields.items():
            if fname in self.forced:
                setattr(self.fz.instance, fname, self.forced[fname])
                continue
            if accessor in self.skipped:
                continue

            self.fuzzM2M(fname, accessor)
            self.DONE.append((fname, accessor))
    
        self.save()

    def fuzzFK(self, fname, field):
        hsh = id(field)
        parent = field.related.parent_model
        if hsh not in Fuzzer.FKREGISTRY:
            if parent.__name__ in Fuzzer.MDLREGISTRY:
                fuzzedMdl = Fuzzer.MDLREGISTRY[parent.__name__]
                setattr(self.fz.instance, fname, fuzzedMdl)
            else:
                fuzz = Fuzzer(parent)
                setattr(self.fz.instance, fname, fuzz.fz.instance)
                Fuzzer.MDLREGISTRY[fuzz.fz.model.__name__] = fuzz.fz.instance
            Fuzzer.FKREGISTRY[hsh] = field
        else:
            rel = Fuzzer(parent)
            setattr(self.fz.instance, fname, rel.fz.instance)

    def fuzzM2M(self, fname, field):
        hsh = id(field)
        if hsh not in Fuzzer.M2MREGISTRY:
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
                    if isinstance(self.fz.instance, rField):
                        data[rFname] = self.fz.instance
                    elif issubclass(field.model, rField):
                        model_name = field.model.__name__
                        if model_name in Fuzzer.MDLREGISTRY:
                            data[rFname] = Fuzzer.MDLREGISTRY[model_name]
                        else:
                            data[rFname] = Fuzzer(field.model).fz.instance
            
                for val in data.values():
                    val.save()
            
                field.through(**data).save()
                Fuzzer.M2MREGISTRY[hsh] = field

    def fuzzData(self, fname, field):
        if isinstance(field, models.AutoField):
            x = self.fuzzAutoField()
        elif isinstance(field, models.CharField):
            x = self.fuzzCharField()
        elif isinstance(field, models.IntegerField):
            x = self.fuzzIntegerField()
        elif isinstance(field, models.TextField):
            x = self.fuzzTextField()
        elif isinstance(field, models.BooleanField):
            x = self.fuzzBooleanField()
        elif isinstance(field, models.DecimalField):
            x = self.fuzzDecimalField()
        else:
            import pdb; pdb.set_trace()
        setattr(self.fz.instance, fname, x)

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

    def save(self):
        self.fz.save()

    @staticmethod
    def reset():
        Fuzzer.MDLREGISTRY = {}
        Fuzzer.FKREGISTRY = {}
        Fuzzer.M2MREGISTRY = {}

    @classmethod
    def evolve(cls):
        pass