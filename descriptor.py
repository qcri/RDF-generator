from json_object import JsonReader


class Descriptor:

    def __init__(self, desc_file):
        self.desc_dict = JsonReader.get_as_dict(desc_file)
        self.prefixes = {}
        self.entities = {}      # Dictionary entity name => uri

    def get_all_prefixes(self):
        return self.desc_dict.get('/prefixes')

    def get_prefix_uri(self, prefix):
        return self.desc_dict.get('/prefixes/{}'.format(prefix))

    def get_graph_uri(self):
        return self.desc_dict.get('/graph')

    def get_all_entities(self):
        return self.desc_dict.get('/entities')

    def get_entity(self, entity_name):
        return self.desc_dict.get('/entities/{}'.format(entity_name))

    def get_entity_uri_template(self, entity_name):
        return self.desc_dict.get('/entities/{}/template'.format(entity_name))

    def get_entity_path(self, entity_name):
        return self.desc_dict.get('/entities/{}/path'.format(entity_name))

    def get_all_entity_features(self, entity_name):
        return self.desc_dict.get('/entities/{}/features'.format(entity_name))

    def get_entity_feature(self, entity_name, feature_path):
        return self.desc_dict.get('/entities/{}/features/{}'.format(entity_name, feature_path))

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
    def construct_uri_from_template(substitutions, uri_template):
        substituted = uri_template

        for path, sub in substitutions.items():
            to_sub = '{{{}}}'.format(path)
            substituted = substituted.replace(to_sub, sub)

        return substituted
