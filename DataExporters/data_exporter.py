"""
stores triples into rdf graphs and exports them in multiple formats
"""

import multiprocessing as mp
import os
import pickle
import time

from DataTransformers.Entity import *
from manager.transformation_metrics import ExportationBatchInfo, TimeStampMessage
from utils.convenience import vectorize_object, create_directory

GRAPH_MAX_SIZE = 1000000


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

    all_formats = [Turtle, XML, PRETTYXML, N3, NT, TRIG, TRIX, NQUADS]

    @staticmethod
    def is_recognized_format(format):
        return format in RDFExportFormats.all_formats


class DataExporter:
    """
    accepts messages of RDFTriples, stores them and when the graph reaches a certain size defined by
    GRAPH_MAX_SIZE, it exports it to the disk
    """

    exporter_no = 0

    def __init__(self, manager, stats_queue, input_queue=None):
        """
        initializes the exporter object
        :param manager: TransformationManager object to read some parameters from such as graph identifier, exportation
        format, the output file name ... etc
        :param stats_queue: multiprocessing.Queue to send statistics messages to the TransformationMetrics object
        :param input_queue: the multiprocessing.Queue where the transformer sends processed records on. This is where
        the triples are received
        """
        self.input_queue = input_queue if input_queue is not None else mp.Queue()
        self.stats_queue = stats_queue
        self.filepath = manager.output_file if manager.output_file is not None else manager.graph_iden
        self.graph_identifier = manager.graph_identifier
        self.export_format = manager.export_format
        self.graph = rdflib.Graph(store='IOMemory', identifier='Twitter')
        self.runner = mp.Process(target=self.run, args=(self.input_queue, self.stats_queue, ))
        self.save_counter = 0
        self.exporter_no = DataExporter.get_next_exporter_no()
        self.buffer_size = manager.buffer_size
        self.triples_buffer = []

    def run(self, input_queue, stats_queue):
        """
        the exporter thread entry point
        :param input_queue: the input queue where the triples are receieve from the transformers
        :param stats_queue: the statistics queue where all stats messages are passed to the TransformationMetrics object
        :return: None
        """
        self.stats_queue = stats_queue
        self.__send_stats_obj(TimeStampMessage(self.exporter_no, 'exporter', 'start', time.time()))

        while True:
            message = pickle.loads(input_queue.get())

            if type(message) is EndMessage:
                self.finish_exportation()
                break
            else:
                self.receive_triples(message)

    def receive_triples(self, message):
        """
        start processing received triples
        :param message: list of RDFTriple objects
        :return: None
        """
        message = vectorize_object(message)
        self.triples_buffer += message
        self.save_if_needed()

    def force_save(self, message):
        """
        bypasses the graph size limit and forces save the current graph to the disk. This is needed in the case when
        a transformer is done its job while the number of triples in the graph is still below the saving threshold
        :param message: list of RDFTriple objects
        :return: None
        """
        message = vectorize_object(message)
        self.triples_buffer += message
        self.save()
        self.graph.close()
        self.graph = rdflib.Graph(identifier=self.graph_identifier)

    def finish_exportation(self):
        """
        flushes the triples buffer to the graph and saves the graph to disk. It also signals that the exporter finished
        its job and will exit
        :return: None
        """
        self.save()
        self.__send_stats_obj(TimeStampMessage(self.exporter_no, 'exporter', 'end', time.time()))
        self.__send_stats_obj(EndMessage('END'))

    def flush_buffer_to_graph(self):
        """
        flushes the records buffer to the rdflib.Graph object and resets the triples buffer
        :return:
        """
        for triple in self.triples_buffer:
            self.graph.add(triple.to_tuple())
        self.triples_buffer = []

    def start(self):
        """
        starts the exporter process if inline_exporters flag is disabled
        :return:
        """
        self.runner.start()

    def save(self, filepath=None, export_format=None):
        """
        flushes the triples buffer to the rdflib.Graph object and saves the whole graph to disk
        :param filepath: the exportation file path
        :param export_format: the exportation format as defined in RDFExportFormats
        :return: None
        """
        self.flush_buffer_to_graph()

        if len(self.graph) > 0:
            fp = filepath if filepath is not None else self.filepath
            create_directory(fp)
            fp = self.get_next_filename(fp)
            exp_format = export_format if export_format is not None else self.export_format

            print('saving {} triples to {}'.format(len(self.graph), fp))

            try:
                self.graph.serialize(fp, exp_format)
            except Exception as ex:
                print(str(ex))

            self.__send_stats_obj(ExportationBatchInfo(self.exporter_no, self.save_counter, len(self.graph)))

    def save_if_needed(self, filepath=None, export_format=None):
        """
        if the graph size goes beyond the save threshold (GRAPH_MAX_SIZE), this methods spills the graph to disk and
        reinitializes the rdflib.Graph object
        :param filepath: the file path to spill the graph to on disk
        :param export_format: the exportation format as defined in RDFExportFormats
        :return: None
        """
        if len(self.graph) > GRAPH_MAX_SIZE:
            self.save(filepath, export_format)
            self.graph.close()
            self.graph = rdflib.Graph(identifier=self.graph_identifier)

    def get_next_filename(self, filepath=None):
        """
        since the graph is saved in batches, this method, whenever called, returns sequential file names based on the
        passed export file path
        :param filepath: the exportation file path
        :return: None
        """
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

    def __send_stats_obj(self, stats_obj):
        self.stats_queue.put(pickle.dumps(stats_obj))

    @staticmethod
    def get_next_exporter_no():
        DataExporter.exporter_no += 1
        return DataExporter.exporter_no
