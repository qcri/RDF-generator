"""
Unlimited levels of dictionaries with an interface to access and assign values via keypaths
"""

import anytree
from utils.convenience import vectorize_object, devectorize_list


class MultilevelDictionaryException(Exception):
    pass


class MultilevelDictionaryKeyPathMatch:

    def __init__(self, keypath, match):
        self.keypath = keypath
        self.match = match


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
        kp_components = MultilevelDictionary.__get_keypath_list(keypath)
        parent_keypath = '/'.join(kp_components[:-1])
        last_kp_component = kp_components[-1]

        insertion_object = MultilevelDictionary.get(self.dict, parent_keypath)

        if type(insertion_object) is not list:
            insertion_object = insertion_object.match

            if type(insertion_object) is dict:
                insertion_object[last_kp_component] = value
            elif type(insertion_object) is list:
                insertion_object.append(value)
            else:
                raise MultilevelDictionaryException('Insertions are not allowed in non collection objects')

    def get(self, keypath):
        if MultilevelDictionary.__is_keypath(keypath):
            return MultilevelDictionary.get_from_dict(self.dict, keypath)
        else:
            return self.dict[keypath] if keypath in self.dict else None

    def keypath_exists(self, keypath):
        """
        checks if the passed key path exists in the dictionary
        :param keypath: key path to check
        :return: True if the key path exists, False otherwise
        """
        return MultilevelDictionary.get(self.dict, keypath) is not None

    def __getitem__(self, item):
        return self.get(item)

    def __contains__(self, item):
        return item in self.dict

    @staticmethod
    def get_from_dict(dictionary, keypath):
        """
        retrieves a list of matches from the dictionary at the specified key path
        :param dictionary: the dictionary to operate on and retrieve the keypath value from
        :param keypath: the key path to get the value at
        :return: list of MultilevelDictionaryKeyPathMatch if key_path exists in the dictionary, empty list otherwise
        """
        if keypath == '/':
            return [MultilevelDictionaryKeyPathMatch(keypath, dictionary)]

        current_object = dictionary

        tree_root, kp_list = MultilevelDictionary.__build_keypath_expansion_tree(keypath, current_object)
        keypath_tree_results = []
        MultilevelDictionary.__get_keypath_results(kp_list, keypath_tree_results, tree_root)

        if len(keypath_tree_results) == 0:
            print('key path {} has no matches in the MultilevelDictionary'.format(keypath))

        return [MultilevelDictionaryKeyPathMatch(node.keypath, node.keypath_value) for node in keypath_tree_results
                if node.keypath_value is not None]

    @staticmethod
    def __get_keypath_results(kp_list, results_list, tree_node):
        """
        this method accepts the path expansion tree and extracts the matches found for the key path which are the leaf
        nodes in the expansion tree
        :param kp_list: the original keypath as list to make sure leaf nodes fulfills the whole path
        :param results_list: list to store the matched results
        :param tree_node: the key path expansion tree
        :return: None. The results are stored in the results_list
        """
        for child in tree_node.children:
            if child.is_leaf and MultilevelDictionary.__node_path_fulfills_keypath(child, kp_list):
                results_list.append(child)
            else:
                MultilevelDictionary.__get_keypath_results(kp_list, results_list, child)

    @staticmethod
    def __node_path_fulfills_keypath(node, kp_list):
        return node.tree_level == len(kp_list)

    @staticmethod
    def __build_keypath_expansion_tree(key_path, collection_obj):
        """
        given a keypath, this static method accepts a key path string and a collection object of nested lists and dicts.
        It returns a tree structure of all possible and valid paths from key path within the collection object
        :param key_path: the key path used to construct the key path tree
        :param collection_obj: the collection object where the key path is applied on
        :return: the root of the constructed key path tree
        """
        kp_list = MultilevelDictionary.__get_keypath_list(key_path)
        kp_root_node = anytree.AnyNode(keypath='/', keypath_value=None, tree_level=0)
        MultilevelDictionary.__expand_keypath(kp_root_node, kp_list, collection_obj)

        return kp_root_node, kp_list

    @staticmethod
    def __expand_keypath(parent_node, kp_list, collection_obj):
        first_kp_comp = kp_list[0] if len(kp_list) > 0 else None

        if first_kp_comp is None or collection_obj is None or \
           not MultilevelDictionary.__is_valid_keypath_component(first_kp_comp, collection_obj):
            return

        if type(collection_obj) is list and MultilevelDictionary.__is_list_path_component(first_kp_comp):
            index_str = first_kp_comp[1:-1]

            if index_str == '*':
                for i, item in enumerate(collection_obj):
                    node = anytree.AnyNode(parent_node, keypath='{}{}/'.format(parent_node.keypath, str(i)),
                                           keypath_value=item, tree_level=parent_node.tree_level + 1)
                    MultilevelDictionary.__expand_keypath(node, kp_list[1:], item)
            else:
                try:
                    index = int(index_str)

                    if index < len(collection_obj):
                        node = anytree.AnyNode(parent_node, keypath='{}{}/'.format(parent_node.keypath, str(index)),
                                               keypath_value=collection_obj[index],
                                               tree_level=parent_node.tree_level + 1)
                        MultilevelDictionary.__expand_keypath(node, kp_list[1:], collection_obj[index])
                except IndexError as ex:
                    # TODO: handle if the index format is invalid
                    raise ex

        elif type(collection_obj) is dict and first_kp_comp in collection_obj:
            node = anytree.AnyNode(parent_node, keypath='{}{}/'.format(parent_node.keypath, first_kp_comp),
                                   keypath_value=collection_obj[first_kp_comp],
                                   tree_level=parent_node.tree_level + 1)
            MultilevelDictionary.__expand_keypath(node, kp_list[1:], collection_obj[first_kp_comp])

    @staticmethod
    def __is_valid_keypath_component(kp_component, collection_obj):
        return MultilevelDictionary.__is_list_path_component(kp_component) or \
                kp_component in collection_obj

    @staticmethod
    def __is_list_path_component(kp_comp):
        return kp_comp.startswith('[') and kp_comp.endswith(']') and (kp_comp[1:-1].isdigit() or kp_comp[1:-1] == '*')

    @staticmethod
    def __is_keypath(kp):
        return '/' in kp

    @staticmethod
    def __get_keypath_list(key_path):

        kp_components = key_path.split('/')

        if key_path.startswith('/'):
            kp_components = kp_components[1:]

        if key_path.endswith('/'):
            kp_components = kp_components[:-1]

        return kp_components
