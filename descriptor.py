from json_object import JsonReader
from utils.MultilevelDictionary import MultilevelDictionary
from utils.convenience import vectorize_object, devectorize_list
import rdflib


class DescriptorException(Exception):
    pass


class Descriptor:
    """
    wraps the descriptor information with a set of convenience funtions to retrieve various descriptor parameters such as
    the list of prefixes and entities with their uri templates, properties ... etc
    """
    def __init__(self, desc_file):
        """
        initializes the descriptor object given the descriptor file path. The descriptor file is json which is loaded
        as dictionary and wrapped in a MultilevelDictionary object in order to retrieve objects and values given
        key paths in the loaded collection hierarchy
        :param desc_file: the descriptor's file path
        """
        self.desc_dict = MultilevelDictionary(JsonReader.get_as_dict(desc_file))
        self.prefixes = {}
        self.namespaces = {}
        self.entities = {}      # Dictionary entity name => uri
        self.descriptor_types = {}

        if self.desc_dict is not None:
            self.load_prefixes()
            self.load_entities()

    def load_prefixes(self):
        self.prefixes = self.load_all_prefixes()
        self.namespaces = {key: rdflib.Namespace(val) for key, val in self.prefixes.items()}

    def load_entities(self):
        self.entities = self.get_all_entities()
        self.descriptor_types = {entity['type']: en_name for en_name, entity in self.entities.items()}

    def load_all_prefixes(self):
        if 'prefixes' in self.desc_dict:
            return self.desc_dict['prefixes']

    def get_prefix_uri(self, prefix):
        return self.get_prefix(prefix)

    def get_prefix(self, prefix):
        if prefix in self.prefixes:
            return self.prefixes[prefix]

    def get_namespace(self, prefix):
        if prefix in self.namespaces:
            return self.namespaces[prefix]
        else:
            raise DescriptorException('undefined prefix {}. Only prefixes defined in the descriptor\'s prefixes section can be used'.format(prefix))

    def get_graph_uri(self):
        if 'graph' in self.desc_dict:
            return self.desc_dict['graph']
        # return self.desc_dict.get('/graph').match

    def get_all_entities(self):
        if 'entities' in self.desc_dict:
            return self.desc_dict['entities']
        # return self.desc_dict.get('/entities').match

    def get_entity(self, entity_name):
        if entity_name in self.entities:
            return self.entities[entity_name]
        # return self.desc_dict.get('/entities/{}'.format(entity_name)).match

    def get_entity_uri_template(self, entity_name):
        if entity_name in self.entities and 'uri_template' in self.entities[entity_name]:
            return self.entities[entity_name]['uri_template']
        # return self.desc_dict.get('/entities/{}/template'.format(entity_name)).match

    def build_entity_uri(self, entity_name, record_dict):
        uri_template = self.get_entity_uri_template(entity_name)
        uri_pathes = Descriptor.extract_variables_from_uri_template(uri_template)

        sub_dict = {}
        subs_count = 0
        for path in uri_pathes.keys():
            path_vals = [val.match for val in vectorize_object(record_dict.get(path))]
            if subs_count == 0 or subs_count == len(path_vals):
                subs_count = len(path_vals)
            else:
                raise Exception('all variables in uri template {} must have the same number of substitutions'.format(uri_template))
            sub_dict[path] = path_vals

        return Descriptor.construct_uri_from_template(sub_dict, uri_template, subs_count)

    def get_entity_path(self, entity_name):
        if entity_name in self.entities and 'path' in self.entities[entity_name]:
            return self.entities[entity_name]['path']
        # return self.desc_dict.get('/entities/{}/path'.format(entity_name)).match

    def get_entity_type(self, entity_name):
        if entity_name in self.entities and 'type' in self.entities[entity_name]:
            return self.entities[entity_name]['type']
        # return self.desc_dict.get('/entities/{}/type'.format(entity_name)).match

    def get_all_entity_features(self, entity_name):
        if entity_name in self.entities and \
           'properties' in self.entities[entity_name]:
            return self.entities[entity_name]['properties']
        # return self.desc_dict.get('/entities/{}/properties'.format(entity_name)).match

    def get_entity_feature(self, entity_name, feature_path):
        if entity_name in self.entities and \
           'properties' in self.entities[entity_name] and \
           feature_path in self.entities[entity_name]['properties']:
            return self.entities[entity_name]['properties'][feature_path]
        # return self.desc_dict.get('/entities/{}/properties/{}'.format(entity_name, feature_path)).match

    def entity_with_type(self, entity_type):
        if entity_type in self.descriptor_types:
            return self.descriptor_types[entity_type]

    @staticmethod
    def extract_variables_from_uri_template(uri_template):
        """
        given a uri template, this method returns the path variables included in the template in addition to their
        locations within the template
        :param uri_template: the uri template to extract path variables from
        :return: {'path1': (start_index, end_index), 'path2': (start_index, end_index) ... }
        """
        template_paths = {}
        idx = 0
        while idx < len(uri_template):
            while idx < len(uri_template) and uri_template[idx] != '{':
                idx += 1
            start_index = idx

            while idx < len(uri_template) and uri_template[idx] != '}':
                idx += 1
            end_index = idx

            if start_index != end_index:
                path = uri_template[start_index + 1:end_index]
                template_paths[path] = (start_index + 1, end_index - 1)

            idx += 1

        return template_paths

    @staticmethod
    def construct_uri_from_template(substitutions, uri_template, subs_count=1):
        """
        given a uri template and a dictionary mapping each template's variable name to it's substitution value, this
        method replaces the template variables with the passed subs and constructs the entities URI
        :param substitutions: dictionary mapping uri template variable to it's actual value {'/path/': ['value1', 'value2' ...etc]}
        :param uri_template: the entities uri template in form 'http://example/com#{/path/var/1}/ex/{/path/var/2}'
        :param subs_count: The number of uris that will be returned after the substitution
        :return: list of URIs [URI]
        """
        if subs_count == 0:
            return []

        uris = [uri_template for _ in range(subs_count)]

        for path, subs in substitutions.items():
            for i in range(len(uris)):
                to_sub = '{{{}}}'.format(path)
                sub = subs[i]
                uris[i] = uris[i].replace(to_sub, sub if type(sub) is str else str(sub))

        return devectorize_list(uris)

    @staticmethod
    def get_relative_path(path, relative_to_path):
        """
        returns the relative path components for path relative to relative_to_path
        :param path: the absolute path to get its relative components
        :param relative_to_path: the base reference path
        :return: relative path components for path relative to relative_to_path as string
        """
        r_path = path.replace(relative_to_path, '', 1)
        return r_path if r_path.startswith('/') else '/{}'.format(r_path)
