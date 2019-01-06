"""
stores triples into rdf graphs and exports them in multiple formats
"""

import rdflib
import os
import pickle
from triples import *
from utils.convenience import vectorize_object, create_directory
import multiprocessing as mp

GRAPH_MAX_SIZE = 10000000


class RDFExportFormats:
    """
    'xml', 'n3', 'turtle', 'nt', 'pretty-xml', 'trix', 'trig' and 'nquads' are supported by rdflib
    """
    Turtle = 'turtle'
    XML = 'xml'
    PRETTYXML = 'pretty-xml'
    NT = 'nt'
    N3 = 'n3'
    TRIX = 'trix'
    TRIG = 'trig'
    NQUADS = 'nquads'


class DataExporter:
    """
    accepts messages of RDFTriples, stores them and when the graph reaches a certain size it exports it
    """

    def __init__(self, manager, exporter_no=0, input_queue=None):
        self.input_queue = input_queue if input_queue is not None else mp.Queue()
        self.filepath = manager.output_file if manager.output_file is not None else manager.graph_iden
        self.graph_identifier = manager.graph_identifier
        self.export_format = manager.export_format
        self.graph = rdflib.Graph(store='IOMemory', identifier='Twitter')
        self.runner = mp.Process(target=self.run, args=(self.input_queue, ))
        self.save_counter = 0
        self.exporter_no = exporter_no
        self.buffer_size = manager.buffer_size
        self.triples_buffer = []

    def run(self, input_queue):
        while True:
            message = pickle.loads(input_queue.get())

            if type(message) is EndMessage:
                self.save()
                break
            else:
                self.receive_triples(message)

    def receive_triples(self, message):
        message = vectorize_object(message)
        self.triples_buffer += message
        self.save_if_needed()

    def flush_buffer(self):
        for triple in self.triples_buffer:
            self.graph.add(triple.to_tuple())
        self.triples_buffer = []

    def start(self):
        self.runner.start()

    def save(self, filepath=None, export_format=None):
        self.flush_buffer()

        fp = filepath if filepath is not None else self.filepath
        create_directory(fp)
        fp = self.get_next_filename(fp)
        exp_format = export_format if export_format is not None else self.export_format

        try:
            self.graph.serialize(fp, exp_format)
        except Exception as ex:
            print(str(ex))

    def save_if_needed(self, filepath=None, export_format=None):

        if len(self.graph) >= GRAPH_MAX_SIZE:
            self.save(filepath, export_format)
            self.graph.close()
            self.graph = rdflib.Graph(identifier=self.graph_identifier)

    def get_next_filename(self, filepath=None):
        fp = filepath if filepath is not None else self.filepath
        directory = os.path.dirname(fp)
        basename = os.path.basename(fp)
        self.save_counter += 1

        if '.' in basename:
            filename = '.'.join(basename.split('.')[:-1])
            extension = basename.split('.')[-1]
            return '{}/{}/{}_{}_{}.{}'.format(directory, basename, filename, self.exporter_no, self.save_counter, extension)
        else:
            filename = basename
            return '{}/{}_{}.{}'.format(directory, filename, self.save_counter, self.export_format)
