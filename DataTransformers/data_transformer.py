import multiprocessing as mp
import pickle
from triples import *
from utils.MultilevelDictionary import MultilevelDictionary
from descriptor import Descriptor
from utils.convenience import vectorize_object, devectorize_list


class DataTransformer:
    """
    takes one data record and transforms it to a list of triples
    """
    def __init__(self, manager, out_queue=None):
        self.manager = manager
        self.descriptor = manager.descriptor
        self.in_queue = mp.Queue()
        self.out_queue = out_queue
        self.exporter = None
        self.buffer_size = manager.buffer_size
        self.records_buffer = []
        self.runner = mp.Process(target=self.run, args=(self.in_queue, ))

    def run(self, in_queue):
        while True:
            msg = in_queue.get()
            message = pickle.loads(msg)

            if type(message) is EndMessage:
                self.transform_records()
                self.out_queue.put(msg)
                break
            else:
                message = message if type(message) is list else [message]
                self.records_buffer += message
                self.transform_records_if_needed()

    def transform_records_if_needed(self):
        if len(self.records_buffer) >= self.buffer_size:
            self.transform_records()

    def transform_records(self):
        triples = []
        for record in self.records_buffer:
            record_triples = self.transform(record)
            triples += record_triples

        self.records_buffer = []
        self.forward_created_triples(triples)

    def transform(self, record):

        record_dict = MultilevelDictionary(record)
        record_triples = []

        for en_name in self.descriptor.entities.keys():
            ent_uris = self.descriptor.build_entity_uri(en_name, record_dict)
            ent_type = self.descriptor.get_entity_type(en_name)

            for ent_uri in vectorize_object(ent_uris):

                entity = Entity(en_name, ent_uri, ent_type, self.descriptor)

                for feature_path, predicates in self.descriptor.get_all_entity_features(en_name).items():
                    object_values = record_dict.get(feature_path)
                    object_values = vectorize_object(object_values)

                    if len(object_values) > 0:
                        sorted_predicates = sorted(predicates, key=lambda p: p['score'])
                        predicate = sorted_predicates[-1]
                        predicate_uri = predicate.get('predicate', None)
                        object_type = predicate.get('object_type', None)
                        object_data_type = predicate.get('data_type', None)

                        obj_entity_name = self.descriptor.entity_with_type(object_data_type)

                        for obj_val in object_values:
                            obj_val_match = obj_val.match

                            if obj_val_match is None:
                                continue

                            if obj_entity_name is not None:     # if the object is an entity
                                obj_ml_dict = MultilevelDictionary(obj_val_match)
                                subs = predicate['substitutions']
                                subs_processed = {}
                                subs_count = 0

                                for key, val in subs.items():
                                    path = key if len(val) == 0 else val
                                    path = Descriptor.get_relative_path(path, feature_path)
                                    subs_processed[key] = [x.match for x in obj_ml_dict.get(path) if x.match is not None]
                                    subs_count = len(subs_processed[key])
                                    if subs_count == 0:
                                        break

                                obj_uri_template = self.descriptor.get_entity_uri_template(obj_entity_name)
                                object_val = Descriptor.construct_uri_from_template(subs_processed, obj_uri_template,
                                                                                    subs_count) if subs_count > 0 else \
                                                                                    None
                            else:                               # if the object is literal
                                object_val = obj_val_match

                            entity.add_feature(predicate_uri, object_val, object_type, object_data_type)

                record_triples += entity.triples

        return record_triples

    def forward_created_triples(self, triples):
        if len(triples) > 0:
            if self.manager.inline_exporters:
                self.exporter.receive_triples(triples)
            else:
                self.out_queue.put(pickle.dumps(triples))

    def start(self):
        self.runner.start()

    def connect_to_exporter(self, exporter):
        if self.manager.inline_exporters:
            self.exporter = exporter
        else:
            self.out_queue = exporter.input_queue

    def send_me_message(self, record):
        if record is not None:
            self.in_queue.put(pickle.dumps(record))

    def return_rdf_triples(self, triples):
        self.out_queue.put(pickle.dumps(triples))
