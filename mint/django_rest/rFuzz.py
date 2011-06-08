import random
from django.db import models
import inspect
from django.db.models.loading import cache

class ValidationError(Exception):
    pass

# def fuzzIt(module, n=100):
#     models = dict((m.__name__, m) for m in module.__dict__.values() if inspect.isclass(m))
# 
#     def _fuzzIt(module):
#         for mname, model in models.items():
#             try:
#                 f = Fuzzer(model)
#                 f.instance.save()
#             except Exception, e:
#                 print "Couldn't fuzz model %s: %s " % (model, e)
#             print 'Fuzzed %s' % model
#             # Fuzzer.FKREGISTRY = {}
#     for i in range(n):
#         _fuzzIt(module)
    
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
    
    # for f in collected:
    #     doDelete = False
    #     for fname, field in f.fields.items():
    #         for i in Fuzzer.integers:
    #             model_cls = f.instance.__class__
    #             try:
    #                 m = model_cls.objects.get(pk=i)
    #                 attr = getattr(m, fname)
    #                 try:
    #                     getattr(model_cls, fname).objects.get(pk=attr)
    #                     # import pdb; pdb.set_trace()
    #                 except:
    #                     getattr(model_cls, fname).field.model.objects.get(**{fname:attr})
    #                     # import pdb; pdb.set_trace()
    #             except:
    #                 try:
    #                     f.instance.delete()
    #                 except:
    #                     pass
    #                 doDelete = True
    #                 break
            # if doDelete:
            #     break

            # 
            # attr = {field.column:getattr(f.instance, field.column)}
            # qs = f.instance.__class__.objects.filter(**attr)
            # if qs:
            #     pass
            # else:
            #     f.instance.delete()
            #     break
    




def validate(fuzz):
    for fname, field in fuzz.fields.items():
        attr = {field.column:getattr(fuzz.instance, field.column)}
        passed = {}
        try:
            qs = fuzz.instance.__class__.objects.filter(**attr)
            passed[fname] = qs[0]
        except:
            raise ValidationError('Get failed')
        return passed


# class Fuzzer(object):
#     
#     integers = range(0, 1000)
#     strings = ['abc', 'def', 'ghi', 'jkl', 'mno', 'pqr', 'stu']
#     words = ['the', 'crazy', 'bird', 'walks', 'off', 'pier']
#     
#     FKREGISTRY = {}
#     MDLREGISTRY = {}
#     
#     def __init__(self, model, skip=None, force=None):
#         self.instance = model if isinstance(model, models.Model) else model()
#         self.skipped = skip if skip else []
#         self.forced = force if force else {}
#         self.fields = dict((f.name, f) for f in self.instance._meta.fields)
# 
#         Fuzzer.MDLREGISTRY[self.instance.__class__.__name__] = self.instance
#         
#         DONE = []
#         for fname, field in self.fields.items():
#             
#             DONE.append(field)
#             
#             if fname in self.forced:
#                 setattr(self.instance, fname, self.forced[fname])
#                 continue
#             elif field in self.skipped:
#                 break
# 
#             if isinstance(field, models.ForeignKey):
#                 hsh = id(field)
#                 if hsh not in Fuzzer.FKREGISTRY:
#                     parent_name = field.related.parent_model.__name__
#                     if parent_name in Fuzzer.MDLREGISTRY:
#                         fuzzed_model = Fuzzer.MDLREGISTRY[parent_name]
#                         setattr(self.instance, fname, fuzzed_model)
#                     else:
#                         parent = field.related.parent_model
#                         fuzz = Fuzzer(parent)
#                         setattr(self.instance, fname, fuzz.instance)
#                         Fuzzer.MDLREGISTRY[parent.__name__] = parent
#                     Fuzzer.FKREGISTRY[hsh] = field
#                 else:
#                     rel = Fuzzer(self.instance, skip=DONE).instance
#                     break
# 
#             else:
#                 data = self.fuzzData(field)
#                 setattr(self.instance, fname, data)       
#         
#         self.m2m = self.get_m2m_accessor_dict()
#         if self.m2m:
#             for m2mName, m2mAccessor in self.m2m.items():
#                 if hasattr(field, 'through'):
#                     through = field.through
#                     through_fields = dict((f.name, f) for f in through._meta.fields)
#                     related = {}
#                     for tFname, tField in through_fields.items():
#                         if hasattr(tField, 'rel'):
#                             if hasattr(tField, 'to'):
#                                 related[tFname] = tField.rel.to
#                     
#                     data = {}
#                     
#                     for rFname, rField in related.items():
#                         if isinstance(self.instance, rField):
#                             data[rFname] = self.instance
#                         elif issubclass(field.model, rField):
#                             model_name = field.model.__name__
#                             if model_name in Fuzzer.MDLREGISTRY:
#                                 data[rFname] = Fuzzer.MDLREGISTRY[model_name]
#                             else:
#                                 data[rFname] = Fuzzer(field.model).instance
#                     field.through.objects.create(**data).save()
#         
#         self.pk = self.instance.pk
#         # self.instance.save()
#     
#     def get_m2m_accessor_dict(self):
#         m2m_accessors = {}
#         for m in self.instance._meta.get_m2m_with_model():
#             f = m[0]
#             try:
#                 m2m_accessors[f.name] = getattr(self.instance, f.name)
#             except ValueError:
#                 pass
#         return m2m_accessors
#         
#     def fuzzData(self, field):
#         if isinstance(field, models.AutoField):
#             return self.fuzzAutoField()
#         if isinstance(field, models.CharField):
#             return self.fuzzCharField()
#         elif isinstance(field, models.IntegerField):
#             return self.fuzzIntegerField()
#         elif isinstance(field, models.TextField):
#             return self.fuzzTextField()
#         elif isinstance(field, models.BooleanField):
#             return self.fuzzBooleanField()
#         elif isinstance(field, models.DecimalField):
#             return self.fuzzDecimalField()
#         else:
#             import pdb; pdb.set_trace()
# 
#     def fuzzDecimalField(self):
#         return random.choice(Fuzzer.integers)
# 
#     def fuzzAutoField(self):
#         return random.choice(Fuzzer.integers)
# 
#     def fuzzCharField(self):
#         return random.choice(Fuzzer.words)
# 
#     def fuzzIntegerField(self):
#         return random.choice(Fuzzer.integers)
# 
#     def fuzzTextField(self):
#         return random.choice(Fuzzer.words)
# 
#     def fuzzBooleanField(self):
#         return random.choice([True, False])
# 
# 
# 


class FuzzyModel(object):
    def __init__(self, model, *args, **kwargs):
        self.model = model.__class__ if isinstance(model, models.Model) else model
        self.instance = model if isinstance(model, models.Model) else model()
        self.fields = dict((f.name, f) for f in self.instance._meta.fields)

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

    integers = range(0, 1000)
    strings = ['abc', 'def', 'ghi', 'jkl', 'mno', 'pqr', 'stu']
    words = ['the', 'crazy', 'bird', 'walks', 'off', 'pier']

    def __init__(self, model, skip=None, force=None):
        self.fz = FuzzyModel(model)
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

    def fuzzFK(self, fname, field):
        hsh = id(field)
        if hsh not in Fuzzer.FKREGISTRY:
            parent = field.related.parent_model
            if parent.__name__ in Fuzzer.MDLREGISTRY:
                fuzzedMdl = Fuzzer.MDLREGISTRY[parent.__name__]
                setattr(self.fz.instance, fname, fuzzedMdl)
            else:
                fuzz = Fuzzer(parent)
                setattr(self.fz.instance, fname, fuzz.fz.instance)
                Fuzzer.MDLREGISTRY[fuzz.fz.instance.__class__.__name__] = fuzz.fz.instance
            Fuzzer.FKREGISTRY[hsh] = field
        else:
            done = [x[1] for x in self.DONE]
            rel = Fuzzer(self.fz.instance, skip=done)  # pyflakes=ignore

    def fuzzM2M(self, fname, field):
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

            field.through.objects.create(**data).save()

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

    @classmethod
    def evolve(cls):
        pass