import collections


class LocationBuilder(collections.MutableMapping):
    """
    Mapping that works like both a dict and a mutable object, i.e.
    loc = LocationBuilder(street='1600 Amphitheatre Pkwy')
    and
    loc.street returns '1600 Amphitheatre Pkwy'
    """

    def __init__(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)
