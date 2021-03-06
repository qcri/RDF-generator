import os
from datetime import datetime


def vectorize_object(obj):
    """
    if the passed object is a list, it's returned as is. If not, it's wrapped in a list object
    :param obj: object of any type to be wrapped in a list
    :return: list
    """
    return obj if type(obj) is list or obj is None else [obj]


def devectorize_list(l):
    """
    if the passed object has length of 1, the object is unwrapped from the list. Otherwise, the list is returned as is
    :param l: list object o devectorize
    :return: object if len(l) is 1 otherwise l
    """
    return l[0] if len(l) == 1 else l


def create_directory(dir):
    """
    create a directory if not already exists
    :param dir: directory name
    :return: None
    """
    if not os.path.exists(dir):
        os.makedirs(dir)

def convert_to_rdf_datetime(dt_str):
    dt = dt_str[:-len(".000Z")]
    return dt_str

"""
def convert_to_rdf_datetime(dt_str):
    if dt_str is not None:
        dt = datetime.strptime(dt_str, '%a %b %d %H:%M:%S %z %Y')
        if dt is not None:
            return dt.strftime('%Y-%m-%dT%H:%M:%S')
"""