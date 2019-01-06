import os


def vectorize_object(obj):
    return obj if type(obj) is list or obj is None else [obj]


def devectorize_list(l):
    return l[0] if len(l) == 1 else l


def create_directory(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
