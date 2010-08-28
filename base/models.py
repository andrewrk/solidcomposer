from django.db import models
from django.contrib.auth.models import User

import string

def create_url(title, is_unique=None):
    """
    creates a clean and safe url to use based on a name.
    calls is_unique with a candidate to see if it is unique.
    """
    allowed_chars = string.letters + string.digits + r'_-.'
    replacement = '_'

    # break title into url safe string
    safe_title = ''
    for c in title.lower():
        if c in allowed_chars:
            safe_title += c
        else:
            safe_title += replacement

    if is_unique is None:
        return safe_title

    # append digits until it is unique
    suffix = 2
    proposed = safe_title
    while not is_unique(proposed):
        proposed = safe_title + str(suffix)
        suffix += 1

    return proposed

class SerializableModel(models.Model):
    PUBLIC, OWNER, ADMIN = range(3)

    # admin attrs are assumed by default
    PUBLIC_ATTRS = ()
    OWNER_ATTRS = ()

    def process_chains(self, chains):
        forwards = []
        new_chains = []

        for chain in chains:
            pieces = chain.split('.')
            forwards.append(pieces[0])
            if len(pieces) > 1:
                new_chains.append('.'.join(pieces[1:]))

        return (forwards, new_chains)
        
    def process_access(self, access):
        if access == self.OWNER:
            # de-esclate from owner to public when forwarding
            return self.PUBLIC
        else:
            return access

    def to_dict(self, access=PUBLIC, chains=[]):
        forwards, new_chains = self.process_chains(chains)
        new_access = self.process_access(access)

        def has_access(field):
            return access >= self.ADMIN or (field.name in self.PUBLIC_ATTRS and access >= self.PUBLIC) or (field.name in self.OWNER_ATTRS and access >= self.OWNER)

        from django.db.models.fields.related import ManyToManyField, ForeignKey
        opts = self._meta
        accessible_fields = filter(has_access, opts.fields+opts.many_to_many)

        data = {'id': self.pk}
        for field in accessible_fields:
            follow = field.name in forwards
            if isinstance(field, ManyToManyField):
                if self.pk is None:
                    data[field.name] = []
                elif follow:
                    data[field.name] = [obj.to_dict(new_access, new_chains) for obj in field.value_from_object(self)]
                else:
                    data[field.name] = [obj.pk for obj in field.value_from_object(self)]
            elif isinstance(field, ForeignKey):
                id = field.value_from_object(self)
                if id is not None and follow:
                    model = field.related.parent_model
                    instance = model.objects.get(pk=id)
                    if issubclass(model, User):
                        data[field.name] = instance.get_profile().to_dict(new_access, new_chains)
                    else:
                        data[field.name] = instance.to_dict(new_access, new_chains)
                else:
                    data[field.name] = id
            else:
                data[field.name] = field.value_from_object(self)

        return data

    class Meta:
        abstract = True
