"""
Unlimited levels of dictionaries with an interface to access and assign values via keypaths
"""


class MultilevelDictionaryException(Exception):
    pass


class MultilevelDictionary:

    def __init__(self, init_dict=None):
        self.dict = {} if init_dict is None else init_dict

    def put(self, keypath, value):
        """
        assigns the given value to the last key component in the key path
        :param keypath: key path referencing a path in the dictionary. The last component is the new key
        :param value: the value to assign to the key path
        :return: value if the key path exists or None otherwise
        """
        kp_components = MultilevelDictionary.get_keypath_list(keypath)
        parent_keypath = '/'.join(kp_components[:-1])
        last_kp_component = kp_components[-1]

        insertion_object = MultilevelDictionary.get(self.dict, parent_keypath)

        if type(insertion_object) is dict:
            insertion_object[last_kp_component] = value
        else:
            raise MultilevelDictionaryException('Insertions are not allowed in non dictionary objects')

    def keypath_exists(self, keypath):
        """
        checks if the passed key path exists in the dictionary
        :param keypath: key path to check
        :return: True if the key path exists, False otherwise
        """
        return MultilevelDictionary.get(self.dict, keypath) is not None

    def __getitem__(self, item):
        return self.get(item)

    @staticmethod
    def get(dictionary, keypath):
        """
        retrieves a value from the dictionary at the specified key path
        :param keypath: the key path to get the value at
        :return: value if key_path exists in the dictionary, None otherwise
        """
        kp_list = MultilevelDictionary.get_keypath_list(keypath)

        current_dict = dictionary

        for kp_component in kp_list:
            if kp_component in current_dict:
                current_dict = current_dict[kp_component]
            else:
                return None

            if type(current_dict) is not dict:
                if kp_component == kp_list[-1]:
                    return current_dict
                else:
                    return None

    @staticmethod
    def get_keypath_list(key_path):

        kp_components = key_path.split('/')

        if key_path.startswith('/'):
            kp_components = kp_components[1:]

        if key_path.endswith('/'):
            kp_components = kp_components[:-1]

        return kp_components
